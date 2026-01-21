from .intent_parser import parse_weather_intent
from .weather_api import fetch_weather
from .rules import decide_umbrella, decide_wind, decide_comfort
from .formatter import format_weather
from .models import WeatherContext
from .error import UserFacingError


def run_agent(user_input: str) -> str:
    intent = parse_weather_intent(user_input)
    if not intent:
        return "天気に関する質問のみ対応しています。"

    try:
        weather = fetch_weather(intent.city, intent.days)
    except UserFacingError as e:
        return str(e)
    except Exception:
        return "現行システムに問題が発生しています。"

    context = WeatherContext(
        weather=weather,
        umbrella=decide_umbrella(weather),
        wind=decide_wind(weather),
        comfort=decide_comfort(weather),
    )

    return format_weather(context)
    