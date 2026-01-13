import os
import requests
import datetime
from models import WeatherResult

def fetch_current_weather(city: str) -> WeatherResult:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY 未設定")

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&lang=ja&units=metric"
    )

    res = requests.get(url, timeout=10)
    data = res.json()

    if data.get("cod") != 200:
        raise RuntimeError("天気取得失敗")

    return WeatherResult(
        city=city,
        weather=data["weather"][0]["description"],
        temp=data["main"]["temp"],
        type="current",
    )

def fetch_forecast_weather(city: str, days_ahead: int) -> WeatherResult:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY 未設定")

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={api_key}&lang=ja&units=metric"
    )

    res = requests.get(url, timeout=10)
    data = res.json()

    target_date = (
        datetime.date.today() + datetime.timedelta(days=days_ahead)
    ).strftime("%Y-%m-%d")

    for item in data["list"]:
        if item["dt_txt"].startswith(target_date):
            return WeatherResult(
                city=city,
                weather=item["weather"][0]["description"],
                temp=item["main"]["temp"],
                type="forecast",
                date=target_date,
            )

    raise RuntimeError("該当日の予報なし")