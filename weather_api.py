import os
import requests
from datetime import datetime, timedelta, time
from urllib.parse import quote
from models import WeatherResult

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

#======================================
# Geo Coding
#======================================

def resolve_city(city: str) -> tuple[float, float]:
    # 都道府県名の「県」「府」「都」「道」を削除
    prefecture_suffixes = ["県", "府", "都", "道"]
    city_variants = [city]
    
    # 「県」「府」「都」「道」で終わる場合は削除したバージョンも試す
    for suffix in prefecture_suffixes:
        if city.endswith(suffix):
            city_variants.append(city[:-1])  # 最後の1文字（県/府/都/道）を削除
            break
    
    # 各バリエーションで検索を試みる
    for city_variant in city_variants:
        encoded_city = quote(city_variant)
        url = (
            "https://api.openweathermap.org/geo/1.0/direct"
            f"?q={encoded_city},JP&limit=1&appid={OPENWEATHER_KEY}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    
    # すべて失敗した場合
    raise RuntimeError(f"地名「{city}」を解決できません")

#======================================
# Current Weather API
#======================================

def fetch_current_weather(city: str, lat: float, lon: float) -> WeatherResult:
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

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

# ===============================
# Forecast (無料APIフォールバック)
# ===============================

def _fetch_with_5day_api(city: str, lat: float, lon: float, days: int) -> WeatherResult:
    """5 Day / 3 Hour Forecast APIを使用（無料プランで利用可能）"""
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&cnt=40"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # 指定された日数の正午頃のデータを取得
    target_date = datetime.now().date() + timedelta(days=days)
    target_datetime = datetime.combine(target_date, time(hour=12))
    
    # 最も近い時刻のデータを探す
    closest_forecast = None
    min_diff = float('inf')
    
    for forecast in data["list"]:
        forecast_time = datetime.fromtimestamp(forecast["dt"])
        diff = abs((forecast_time - target_datetime).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest_forecast = forecast
    
    if not closest_forecast:
        raise RuntimeError(f"指定された日数（{days}日後）のデータが見つかりません")
    
    return WeatherResult(
        city=city,
        weather=closest_forecast["weather"][0]["description"],
        temp=closest_forecast["main"]["temp"],
        feels_like=closest_forecast["main"]["feels_like"],
        humidity=closest_forecast["main"]["humidity"],
        rain_probability=int(closest_forecast.get("pop", 0) * 100),
        wind_speed=closest_forecast.get("wind", {}).get("speed", 0),
        type="forecast",
    )


def fetch_daily_weather(city: str, days: int) -> WeatherResult:
    lat, lon = resolve_city(city)

    url = (
        "https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )

    response = requests.get(url, timeout=10)
    
    # 401エラーの場合、無料APIにフォールバック
    if response.status_code == 401:
        try:
            return _fetch_with_5day_api(city, lat, lon, days)
        except Exception as e:
            error_data = response.json() if response.text else {}
            error_message = error_data.get("message", "Unauthorized")
            raise RuntimeError(
                f"OpenWeatherMap API認証エラー (401): {error_message}\n\n"
                "OpenWeatherMap API 3.0のOne Call APIを使用するには、"
                "'One Call by Call'サブスクリプションを有効にする必要があります。\n"
                "無料プランでも1,000コール/日まで利用可能です。\n\n"
                "設定手順:\n"
                "1. https://openweathermap.org/api/one-call-3 にアクセス\n"
                "2. 'One Call by Call'サブスクリプションを有効化\n"
                "3. APIキーが正しく設定されているか確認\n\n"
                f"代替APIもエラー: {str(e)}"
            )
    
    response.raise_for_status()
    data = response.json()
    
    # APIエラーのチェック
    if "cod" in data and data["cod"] != 200:
        error_message = data.get("message", "不明なエラー")
        raise RuntimeError(f"OpenWeatherMap APIエラー: {error_message}")
    
    # dailyキーの存在確認
    if "daily" not in data:
        error_message = data.get("message", "APIレスポンスに'daily'キーがありません")
        raise RuntimeError(
            f"OpenWeatherMap APIエラー: {error_message}\n"
            "APIレスポンスの構造が期待と異なります。"
        )
    
    if days >= len(data["daily"]):
        raise RuntimeError(f"指定された日数（{days}日後）は利用できません。利用可能な日数: 0-{len(data['daily'])-1}")
    
    daily = data["daily"][days]

    return WeatherResult(
        city=city,
        weather=daily["weather"][0]["description"],
        temp=daily["temp"]["day"],
        feels_like=daily["feels_like"]["day"],
        humidity=daily["humidity"],
        rain_probability=int(daily.get("pop", 0) * 100),
        wind_speed=daily["wind_speed"],
        type="forecast",
    )

# ===============================
# ② 分岐用 統合関数
# ===============================

def fetch_weather(city: str, days: int) -> WeatherResult:
    lat, lon = resolve_city(city)

    if days == 0:
        return fetch_current_weather(city, lat, lon)

    return fetch_daily_weather(city, days)