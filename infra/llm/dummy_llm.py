# infra/llm/dummy_llm.py
import time
import random

async def dummy_llm_predict(text: str) -> dict:
    """Simulates an LLM call by echoing the input after a short delay.

    Returns:
        dict: A dictionary containing the output text, input tokens, and output tokens.
    """
    # Simulate processing time
    await asyncio.sleep(random.uniform(0.1, 0.5)) # Simulate 100-500ms delay

    output_text = f"Echo: {text}"

    # Simulate token calculation (very basic)
    input_tokens = len(text.split())
    output_tokens = len(output_text.split())

    return {
        "output_text": output_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

# Add asyncio import if not already present at the top
import asyncio
