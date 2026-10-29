"""Part II - fine-tune DistilBERT to classify market-operations tickets.

Trains on data/tickets_train.csv, early-stops on tickets_val.csv and reports on
tickets_test.csv (held-out templates). A TF-IDF + logistic-regression baseline
is trained on the same split so the report can compare before/after.

Usage:  python training/finetune_classifier.py [--epochs 3]
Output: models/ticket-classifier/ (model + tokenizer), reports/classifier_metrics.json,
        reports/confusion_matrix.png
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             classification_report, f1_score)
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          DataCollatorWithPadding, Trainer, TrainingArguments)

ROOT = Path(__file__).resolve().parents[1]
BASE_MODEL = "distilbert-base-uncased"
OUT_DIR = ROOT / "models" / "ticket-classifier"
REPORTS = ROOT / "reports"


def load(split):
    return pd.read_csv(ROOT / "data" / f"tickets_{split}.csv")


def main(epochs):
    torch.manual_seed(42)
    train, val, test = load("train"), load("val"), load("test")
    labels = sorted(train.label.unique())
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}

    # Baseline: TF-IDF + logistic regression
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    lr = LogisticRegression(max_iter=2000).fit(vec.fit_transform(train.text), train.label)
    base_pred = lr.predict(vec.transform(test.text))
    baseline = {"accuracy": accuracy_score(test.label, base_pred),
                "macro_f1": f1_score(test.label, base_pred, average="macro")}
    print("Baseline TF-IDF+LR:", baseline)

    tok = AutoTokenizer.from_pretrained(BASE_MODEL)

    def to_ds(df):
        ds = Dataset.from_pandas(df.assign(labels=df.label.map(label2id))[["text", "labels"]])
        return ds.map(lambda b: tok(b["text"], truncation=True, max_length=128), batched=True)

    ds_train, ds_val, ds_test = to_ds(train), to_ds(val), to_ds(test)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(labels), id2label=id2label, label2id=label2id)

    def compute_metrics(p):
        preds = p.predictions.argmax(-1)
        return {"accuracy": accuracy_score(p.label_ids, preds),
                "macro_f1": f1_score(p.label_ids, preds, average="macro")}

    args = TrainingArguments(
        output_dir=str(ROOT / "models" / "_checkpoints"),
        num_train_epochs=epochs, per_device_train_batch_size=16, per_device_eval_batch_size=32,
        learning_rate=5e-5, weight_decay=0.01,
        warmup_steps=int(0.1 * epochs * -(-len(train) // 16)),  # 10% warm-up
        eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
        metric_for_best_model="macro_f1", save_total_limit=1, logging_steps=25,
        report_to=[], seed=42,
    )
    trainer = Trainer(model=model, args=args, train_dataset=ds_train, eval_dataset=ds_val,
                      data_collator=DataCollatorWithPadding(tok), compute_metrics=compute_metrics)
    trainer.train()

    pred = trainer.predict(ds_test)
    y_pred = pred.predictions.argmax(-1)
    y_true = pred.label_ids
    finetuned = {"accuracy": accuracy_score(y_true, y_pred),
                 "macro_f1": f1_score(y_true, y_pred, average="macro")}
    print("Fine-tuned DistilBERT:", finetuned)
    report = classification_report(y_true, y_pred, target_names=labels, output_dict=True)
    print(classification_report(y_true, y_pred, target_names=labels))

    trainer.save_model(str(OUT_DIR))
    tok.save_pretrained(str(OUT_DIR))

    REPORTS.mkdir(exist_ok=True)
    history = [h for h in trainer.state.log_history if "eval_macro_f1" in h or "loss" in h]
    (REPORTS / "classifier_metrics.json").write_text(json.dumps({
        "base_model": BASE_MODEL, "epochs": epochs,
        "n_train": len(train), "n_val": len(val), "n_test": len(test),
        "baseline_tfidf_lr": baseline, "finetuned_distilbert": finetuned,
        "per_class": {l: report[l] for l in labels}, "log_history": history,
    }, indent=2))

    fig, ax = plt.subplots(figsize=(9, 8))
    ConfusionMatrixDisplay.from_predictions(
        [labels[i] for i in y_true], [labels[i] for i in y_pred],
        labels=labels, xticks_rotation=45, ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Fine-tuned DistilBERT - held-out test tickets")
    fig.tight_layout()
    fig.savefig(REPORTS / "confusion_matrix.png", dpi=150)
    print("Saved model to", OUT_DIR)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    main(ap.parse_args().epochs)
