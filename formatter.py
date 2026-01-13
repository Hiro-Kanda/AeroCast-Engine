import json
from openai import OpenAI
from models import WeatherResult

client = OpenAI()

def format_weather(result: WeatherResult) -> str:
    messages = [
        {
            "role": "system",
            "content": "あなたは天気を分かりやすく説明するアシスタントです。",
        },
        {
            "role": "user",
            "content": json.dumps(result.__dict__, ensure_ascii=False),
        },
    ]

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3,
    )

    return res.choices[0].message.content