import json
from dataclasses import asdict

from openai import OpenAI
from .models import WeatherContext
from .fallback_formatter import simple_format

client = OpenAI()

def format_weather(context: WeatherContext) -> str:
    """
    WeatherContextに含まれる事実データと判断結果を
    自然な日本語で説明する。
    判断・推測は禁止。
    """

    system_prompt = (
        "あなたは天気情報を分かりやすく説明するアシスタントです。"
        "与えられた情報をそのまま説明してください。"
        "新しい判断や推測は行わないでください。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(asdict(context), ensure_ascii=False),
        },
    ]

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.3,
        )
        return res.choices[0].message.content
    except Exception:
        # LLM 障害時フォールバック
        return simple_format(context)
