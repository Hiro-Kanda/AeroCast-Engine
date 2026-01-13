from intent_parser import parse_weather_intent
from weather_api import fetch_current_weather, fetch_forecast_weather
from formatter import format_weather
from openai import OpenAI

client = OpenAI()

def run_agent(user_input: str) -> str:
    intent = parse_weather_intent(user_input)

    if intent:
        if intent.days == 0:
            result = fetch_current_weather(intent.city)
        else:
            result = fetch_forecast_weather(intent.city, intent.days)
        return format_weather(result)

    # fallback
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": user_input}],
    )
    return res.choices[0].message.content