import httpx
import asyncio

GROQ_API_KEY = "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"
async def _call_llm( prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",  # or mixtral-8x7b-32768
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
            )
        return resp.json()["choices"][0]["message"]["content"].strip()
res = asyncio.run(_call_llm("Return only this JSON, no markups: {\"test\": \"success\"}"))
print(res)