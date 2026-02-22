import os
import asyncio
import httpx
from typing import AsyncGenerator, Optional

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')


async def async_stream_generate(prompt: str, model: Optional[str] = None, max_tokens: int = 512) -> AsyncGenerator[str, None]:
    """Stream tokens from a local Ollama server. Falls back to a simple echo generator if the server is unavailable.

    Yields token strings.
    """
    url = f"{OLLAMA_URL}/api/generate"
    payload = {"prompt": prompt, "max_tokens": max_tokens}
    if model:
        payload['model'] = model

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream('POST', url, json=payload) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_text():
                    # many LLM servers stream text chunks; forward as-is
                    if chunk:
                        yield chunk
        return
    except Exception:
        # fallback: simple simulated streaming by splitting into words
        for tok in prompt.split():
            await asyncio.sleep(0.01)
            yield tok + ' '
