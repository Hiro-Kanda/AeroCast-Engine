import json
from openai import OpenAI
from models import WeatherContext

client = OpenAI()

def format_weather(context: WeatherContext) -> str:
    """
    WeatherContextに含まれる事実データと判断結果を
    自然な日本語で説明する。
    判断・推測は禁止。
    """

    system_prompt = (
        "あなたは天気情報を分かり分かりやすく説明するアシスタントです。"
        "与えられた情報をもとに、事実と判断結果をそのまま説明してください。"
        "新しい判断や推測は行わないでください。"
    )

    user_content = {
        "weather": context.weather.__dict__,
        "umbrella": context.umbrella.__dict__,
        "wind": context.wind.__dict__,
        "comfort": context.comfort.__dict__,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(user_content, ensure_ascii=False),
        }
    ]

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3,
    )

    return res.choices[0].message.content