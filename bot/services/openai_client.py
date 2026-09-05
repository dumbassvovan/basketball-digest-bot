"""Тонкая обёртка над OpenAI API."""

from __future__ import annotations

from openai import OpenAI


def summarize_text(api_key: str, text: str) -> str:
    if not api_key or api_key == "your-openai-api-key":
        raise RuntimeError(
            "Не задан OPENAI_API_KEY. Добавьте ключ в файл .env."
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Кратко перескажи текст на русском, 2–4 предложения.",
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    content = response.choices[0].message.content
    return (content or "").strip()
