from intents import WeatherIntent

DEFAULT_CITY = "Tokyo"


def parse_weather_intent(text: str) -> WeatherIntent | None:
    if "天気" not in text:
        return None

    city_map = {
        "東京": "Tokyo",
        "大阪": "Osaka",
        "名古屋": "Nagoya",
    }

    city = DEFAULT_CITY
    for jp, en in city_map.items():
        if jp in text:
            city = en

    if "明後日" in text:
        return WeatherIntent(city=city, days=2)
    if "明日" in text:
        return WeatherIntent(city=city, days=1)

    return WeatherIntent(city=city, days=0)
