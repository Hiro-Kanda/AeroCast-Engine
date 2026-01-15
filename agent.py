from intent_parser import parse_weather_intent
from weather_api import fetch_weather
from rules import decide_umbrella, decide_wind, decide_comfort
from formatter import format_weather
from models import WeatherContext


def run_agent(user_input: str) -> str:
    intent = parse_weather_intent(user_input)
    if not intent:
        return "天気に関する質問のみ対応しています。"

    weather = fetch_weather(intent.city, intent.days)

    context = WeatherContext(
        weather=weather,
        umbrella=decide_umbrella(weather),
        wind=decide_wind(weather),
        comfort=decide_comfort(weather),
    )

    return format_weather(context)
    