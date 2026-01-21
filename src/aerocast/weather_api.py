import os
import requests
from datetime import datetime, timedelta, time, timezone
from urllib.parse import quote

from .models import WeatherResult
from .error import CityNotFoundError, WeatherAPIError

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_KEY:
    raise WeatherAPIError("OPENWEATHER_API_KEY が設定されていません")

# 日本時間
JST = timezone(timedelta(hours=9))

# requests セッション（再利用）
_SESSION = requests.Session()
_TIMEOUT = 10

# ======================================
# Geo Coding
# ======================================

def resolve_city(city: str) -> tuple[float, float]:
    prefecture_suffixes = ["県", "府", "都", "道"]
    city_variants = [city]

    for suffix in prefecture_suffixes:
        if city.endswith(suffix):
            city_variants.append(city[:-1])
            break

    for city_variant in city_variants:
        encoded_city = quote(city_variant)
        url = (
            "https://api.openweathermap.org/geo/1.0/direct"
            f"?q={encoded_city},JP&limit=1&appid={OPENWEATHER_KEY}"
        )
        try:
            response = _SESSION.get(url, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            raise WeatherAPIError("地名解決APIへの接続に失敗しました")

        if data:
            return data[0]["lat"], data[0]["lon"]

    raise CityNotFoundError(f"地名「{city}」を解決できませんでした")

# ======================================
# Current Weather
# ======================================

def fetch_current_weather(city: str, lat: float, lon: float) -> WeatherResult:
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )

    try:
        response = _SESSION.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        raise WeatherAPIError("現在の天気情報の取得に失敗しました")

    return WeatherResult(
        city=city,
        weather=data["weather"][0]["description"],
        temp=data["main"]["temp"],
        feels_like=data["main"]["feels_like"],
        humidity=data["main"]["humidity"],
        rain_probability=int(data.get("pop", 0) * 100),
        wind_speed=data.get("wind", {}).get("speed", 0),
        type="current",
    )

# ======================================
# Forecast Weather (無料API制約対応)
# ======================================

def fetch_forecast_weather(
    city: str,
    lat: float,
    lon: float,
    days: int,
) -> WeatherResult:
    if not (0 <= days <= 5):
        raise WeatherAPIError("無料APIでは0〜5日後まで取得可能です")

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&cnt=40"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )

    try:
        response = _SESSION.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        raise WeatherAPIError("予報データの取得に失敗しました")

    if "list" not in data:
        raise WeatherAPIError("予報データ形式が不正です")

    now_jst = datetime.now(JST)
    target_date = now_jst.date() + timedelta(days=days)
    target_datetime = datetime.combine(
        target_date,
        time(hour=12),
        tzinfo=JST,
    )

    closest = None
    min_diff = float("inf")

    for item in data["list"]:
        forecast_time = datetime.fromtimestamp(
            item["dt"],
            tz=timezone.utc,
        ).astimezone(JST)

        diff = abs((forecast_time - target_datetime).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest = item

    if not closest:
        raise WeatherAPIError("指定日の予報が見つかりませんでした")

    return WeatherResult(
        city=city,
        weather=closest["weather"][0]["description"],
        temp=closest["main"]["temp"],
        feels_like=closest["main"]["feels_like"],
        humidity=closest["main"]["humidity"],
        rain_probability=int(closest.get("pop", 0) * 100),
        wind_speed=closest.get("wind", {}).get("speed", 0),
        type="forecast",
    )

# ======================================
# Unified Entry
# ======================================

def fetch_weather(city: str, days: int) -> WeatherResult:
    lat, lon = resolve_city(city)

    if days == 0:
        return fetch_current_weather(city, lat, lon)

    return fetch_forecast_weather(city, lat, lon, days)
