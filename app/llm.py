"""Text-generation backend used by the RAG chatbot and the reply drafter.

A small open instruction-tuned model run on CPU with Hugging Face transformers.
Set LOCAL_LLM=<hf model id> to use a different model.
"""
import os
from functools import lru_cache

LOCAL_MODEL = os.getenv("LOCAL_LLM", "Qwen/Qwen2.5-1.5B-Instruct")


def backend() -> str:
    return "local"


def model_name() -> str:
    return LOCAL_MODEL


@lru_cache(maxsize=1)
def _local_pipeline():
    import torch
    from transformers import pipeline
    torch.set_num_threads(os.cpu_count() or 4)
    return pipeline("text-generation", model=LOCAL_MODEL, dtype=torch.float32)


def generate(system: str, messages: list[dict], max_new_tokens: int = 400) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
    pipe = _local_pipeline()
    chat = [{"role": "system", "content": system}] + messages
    out = pipe(chat, max_new_tokens=max_new_tokens, do_sample=False, return_full_text=False)
    return out[0]["generated_text"].strip()
