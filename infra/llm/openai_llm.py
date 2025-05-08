# infra/llm/openai_llm.py
import os
from openai import OpenAI

_client = None
default_model_str = ""
LM_STUDIO_API_BASE_URL = "http://26.126.159.93:22227/v1"


async def predict(text: str) -> dict:
    """Runs a prediction using the OpenAI API."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "sk-your-improvised-api-key"),
            base_url=os.environ.get("OPENAI_BASE_URL", LM_STUDIO_API_BASE_URL)
        )

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

    completion = _client.chat.completions.create(
        model=default_model_str,
        messages=conversation,
    )

    output_text = ""
    if completion.choices:
        output_text = completion.choices[0].message.content or ""

    input_tokens = len(text.split())
    prompt_tokens_api = input_tokens
    if completion.usage:
        prompt_tokens_api = completion.usage.prompt_tokens

    completion_tokens_api = len(output_text.split())
    if completion.usage:
        completion_tokens_api = completion.usage.completion_tokens

    return {
        "output_text": output_text,
        "input_tokens": prompt_tokens_api,
        "output_tokens": completion_tokens_api,
    }

_client = None

# fast test
# import asyncio
# async def main():
#     print(await predict("1233"))
# asyncio.run(main())