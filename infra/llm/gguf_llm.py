# infra/llm/gguf_llm.py
import os
from vllm import LLM, SamplingParams

## NOTE
# qwen3 gguf NOT SUPPORTED in vllm 0.8.5.post1 =(
# _MODEL_PATH =  "/workspace/model_weights/LLM/gguf/lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q4_K_M.gguf"  # os.getenv("LLM_MODEL_PATH", "path/to/qwen3_quant.gguf")

_MODEL_PATH = "/workspace/model_weights/LLM/gguf/lmstudio-community/Qwen2.5-1.5B-Instruct-GGUF/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"


_client = None

async def predict(text: str) -> dict:
    """Runs a Qwen3 quantized gguf model via vLLM."""
    global _client
    if _client is None:
        _client = LLM(model=_MODEL_PATH)
    params = SamplingParams()
    conversation = [
    {
        "role": "system",
        "content": "You are a helpful assistant"
    },
    {
        "role": "user",
        "content": text
    },
    ]
    outputs = _client.chat(conversation, params)
    _client.generate
    output_text = ""
    for output in outputs:
        # prompt = output.prompt
        generated_text = output.outputs[0].text
        output_text += generated_text
    input_tokens = len(text.split())
    output_tokens = len(output_text.split())
    # Generate response asynchronously
    return {
        "output_text": output_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

