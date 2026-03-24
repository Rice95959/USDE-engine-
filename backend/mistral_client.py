"""
Mistral API async client for USDE Clarity Engine.
Uses httpx for async HTTP. Compatible with mistral-large-latest, mistral-small-latest, etc.
"""

import httpx
from typing import Optional


class MistralClient:
    BASE_URL = "https://api.mistral.ai/v1/chat/completions"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(
        self,
        system: str,
        user: str,
        model: str = "mistral-large-latest",
        max_tokens: int = 16000,
        temperature: float = 0.1,
        retries: int = 3,
    ) -> str:
        """Send a chat completion request to Mistral API with retry logic."""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        delays = [0, 2.5, 6.0]
        last_error = None

        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(retries):
                if attempt > 0:
                    import asyncio
                    await asyncio.sleep(delays[attempt])

                try:
                    response = await client.post(
                        self.BASE_URL, headers=headers, json=payload
                    )

                    # Rate limit / overload
                    if response.status_code in (429, 503, 529):
                        last_error = f"HTTP {response.status_code}: rate limited"
                        if attempt < retries - 1:
                            continue
                        raise httpx.HTTPStatusError(
                            last_error, request=response.request, response=response
                        )

                    response.raise_for_status()
                    data = response.json()

                    # Extract text from Mistral response
                    choices = data.get("choices", [])
                    if not choices:
                        raise ValueError("No choices in Mistral response")

                    content = choices[0].get("message", {}).get("content", "")
                    if not content:
                        raise ValueError("Empty content in Mistral response")

                    return content

                except httpx.HTTPStatusError:
                    raise
                except httpx.TimeoutException:
                    last_error = "Request timed out"
                    if attempt == retries - 1:
                        raise
                except Exception as e:
                    last_error = str(e)
                    if attempt == retries - 1:
                        raise

        raise RuntimeError(f"All retries failed: {last_error}")
