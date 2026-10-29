"""Text-generation backend used by the RAG chatbot and the reply drafter.

LLM_BACKEND=claude  -> Anthropic API (claude-opus-5-5); needs ANTHROPIC_API_KEY.
LLM_BACKEND=local   -> a small open model run on CPU with Hugging Face transformers.
Default: claude when ANTHROPIC_API_KEY is set, otherwise local.
"""
import os
from functools import lru_cache

CLAUDE_MODEL = "claude-opus-5-5"
LOCAL_MODEL = os.getenv("LOCAL_LLM", "Qwen/Qwen2.5-1.5B-Instruct")


def backend() -> str:
    return os.getenv("LLM_BACKEND") or ("claude" if os.getenv("ANTHROPIC_API_KEY") else "local")


def model_name() -> str:
    return CLAUDE_MODEL if backend() == "claude" else LOCAL_MODEL


@lru_cache(maxsize=1)
def _local_pipeline():
    import torch
    from transformers import pipeline
    torch.set_num_threads(os.cpu_count() or 4)
    return pipeline("text-generation", model=LOCAL_MODEL, dtype=torch.float32)


@lru_cache(maxsize=1)
def _claude_client():
    import anthropic
    return anthropic.Anthropic()


def generate(system: str, messages: list[dict], max_new_tokens: int = 400) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
    if backend() == "claude":
        resp = _claude_client().beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            system=system,
            messages=messages,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if resp.stop_reason == "refusal":
            return "The model declined to answer this request."
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    pipe = _local_pipeline()
    chat = [{"role": "system", "content": system}] + messages
    out = pipe(chat, max_new_tokens=max_new_tokens, do_sample=False, return_full_text=False)
    return out[0]["generated_text"].strip()
