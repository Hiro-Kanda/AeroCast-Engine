from .models import WeatherContext


def simple_format(context: WeatherContext) -> str:
    w = context.weather
    lines = [
        f"{w.city}の天気:{w.weather}",
        f"気温：{w.temp}℃ (体感 {w.feels_like}℃) ",
        f"湿度：{w.humidity}%",
        f"風速：{w.wind_speed}m/s",
    ]

    if context.umbrella.needed:
        lines.append("傘が必要です。")

    return "\n".join(lines)