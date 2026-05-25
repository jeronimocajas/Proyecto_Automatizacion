import httpx
import json
from core.config import settings

headers = {
    "x-api-key": settings.ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

payload = {
    "model": "claude-haiku-4-5",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "di hola"}]
}

response = httpx.post(
    "https://api.anthropic.com/v1/messages",
    json=payload,
    headers=headers,
)
print("Status:", response.status_code)
print("Response:", response.text[:300])