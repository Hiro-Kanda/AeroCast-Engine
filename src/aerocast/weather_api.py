import os
import requests
from datetime import datetime, timedelta, time, timezone
from typing import Optional, List, Tuple
from urllib.parse import quote

from .models import WeatherResult
from .error import CityNotFoundError, WeatherAPIError
from .logger import logger
from .snow_estimator import estimate_snow_probability
from .retry import exponential_backoff

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_KEY:
    raise WeatherAPIError("OPENWEATHER_API_KEY が設定されていません")

# 日本時間
JST = timezone(timedelta(hours=9))

# requests セッション（再利用）
_SESSION = requests.Session()
_TIMEOUT = 10

# ======================================
# Response Validation
# ======================================

def _validate_weather_response(data: dict) -> None:
    """天気APIレスポンスの構造を検証"""
    if "weather" not in data:
        raise WeatherAPIError("APIレスポンスに必須フィールド 'weather' がありません")
    
    if not data.get("weather") or len(data["weather"]) == 0:
        raise WeatherAPIError("天気情報が取得できませんでした")
    
    if "main" not in data:
        raise WeatherAPIError("APIレスポンスに必須フィールド 'main' がありません")

# ======================================
# Geo Coding
# ======================================

@exponential_backoff(max_retries=3, base_delay=1.0)
def _fetch_geo_data(city_variant: str, limit: int = 5) -> List[dict]:
    """地理情報を取得（リトライ機能付き）"""
    encoded_city = quote(city_variant)
    url = (
        "https://api.openweathermap.org/geo/1.0/direct"
        f"?q={encoded_city},JP&limit={limit}&appid={OPENWEATHER_KEY}"
    )
    response = _SESSION.get(url, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def resolve_city_with_candidates(city: str, limit: int = 5) -> Tuple[Optional[tuple[float, float]], List[str]]:
    """
    都市名を解決し、候補も返す
    
    Returns:
        (座標, 候補リスト) のタプル
        座標が見つかった場合は (lat, lon) と空のリスト
        候補がある場合は None と候補リスト
    """
    prefecture_suffixes = ["県", "府", "都", "道"]
    city_variants = [city]

    for suffix in prefecture_suffixes:
        if city.endswith(suffix):
            city_variants.append(city[:-1])
            break

    all_candidates = []
    
    for city_variant in city_variants:
        try:
            data = _fetch_geo_data(city_variant, limit)
            
            if data:
                # 最初の結果を返す
                lat, lon = data[0]["lat"], data[0]["lon"]
                city_name = data[0].get("name", city)
                
                # 複数の候補がある場合はリストに追加
                if len(data) > 1:
                    for item in data[1:]:
                        candidate_name = item.get("name", "")
                        if candidate_name and candidate_name not in all_candidates:
                            all_candidates.append(candidate_name)
                
                return (lat, lon), all_candidates
            else:
                # データがない場合は次のバリアントを試す
                continue
                
        except requests.RequestException as e:
            logger.error(f"地名解決APIへの接続に失敗しました: {e}", exc_info=True)
            # 次のバリアントを試す
            continue

    # 見つからなかった場合
    return None, all_candidates


def resolve_city(city: str) -> tuple[float, float]:
    """都市名を解決（後方互換性のため）"""
    coords, _ = resolve_city_with_candidates(city, limit=1)
    if coords is None:
        raise CityNotFoundError(f"地名「{city}」を解決できませんでした")
    return coords

# ======================================
# Current Weather
# ======================================

@exponential_backoff(max_retries=3, base_delay=1.0)
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
    except requests.RequestException as e:
        logger.error(f"現在の天気情報の取得に失敗しました: {e}", exc_info=True)
        raise WeatherAPIError("現在の天気情報の取得に失敗しました")

    _validate_weather_response(data)

    return WeatherResult(
        city=city,
        weather=data["weather"][0]["description"],
        temp=data["main"]["temp"],
        feels_like=data["main"]["feels_like"],
        humidity=data["main"]["humidity"],
        # 現在の天気APIにはpopフィールドがないため、0を設定（後でfetch_nowcast_probabilityで上書き）
        rain_probability=int(data.get("pop", 0) * 100),
        wind_speed=data.get("wind", {}).get("speed", 0),
        type="current",
    )

# ======================================
# Forecast Weather (無料API制約対応)
# ======================================

@exponential_backoff(max_retries=3, base_delay=1.0)
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
    except requests.RequestException as e:
        logger.error(f"予報データの取得に失敗しました: {e}", exc_info=True)
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

    # 予報アイテムの検証
    if "weather" not in closest or not closest.get("weather") or len(closest["weather"]) == 0:
        raise WeatherAPIError("予報データの天気情報が不正です")
    if "main" not in closest:
        raise WeatherAPIError("予報データの気象情報が不正です")

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
    """
    天気情報を取得（都市名の解決と候補の取得も行う）
    
    都市名が曖昧な場合は候補を返すために例外を投げる可能性がある
    """
    # まず候補を取得してみる
    coords, candidates = resolve_city_with_candidates(city, limit=5)
    
    if coords is None:
        if candidates:
            # 候補がある場合はCityNotFoundErrorに候補情報を含める
            candidates_str = "、".join(candidates[:5])
            raise CityNotFoundError(
                f"地名「{city}」が曖昧です。どちらですか？\n候補: {candidates_str}"
            )
        else:
            raise CityNotFoundError(f"地名「{city}」を解決できませんでした")
    
    lat, lon = coords

    if days == 0:
        current = fetch_current_weather(city, lat, lon)

        pop, item = fetch_nowcast_probability(lat, lon)
        current.rain_probability = pop

        #snow情報があれば拾う
        _enrich_snow_from_forecast_item(current, item)

        # snow_probabilityが未設定の場合は推定モデルを使用
        if current.snow_probability is None:
            current.snow_probability = estimate_snow_probability(current.rain_probability, current.temp)

        return current
    
    forecast = fetch_forecast_weather(city, lat, lon, days)
    return forecast


@exponential_backoff(max_retries=2, base_delay=0.5)
def fetch_nowcast_probability(lat: float, lon: float) -> tuple[int, Optional[dict]]:
    """forecastの直近枠から降水確率（pop）と、その枠データを返す"""
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&cnt=40"
        f"&appid={OPENWEATHER_KEY}&units=metric&lang=ja"
    )
    try:
        response = _SESSION.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.warning(f"予報データ（nowcast）の取得に失敗しました: {e}", exc_info=True)
        return 0, None
    
    if "list" not in data or not data["list"]:
        return 0, None

    # 現在時刻に最も近い予報データを取得
    now_jst = datetime.now(JST)
    closest = None
    min_diff = float("inf")

    for item in data["list"]:
        forecast_time = datetime.fromtimestamp(
            item["dt"],
            tz=timezone.utc,
        ).astimezone(JST)
        
        # 過去のデータは除外し、現在時刻以降で最も近いものを選択
        diff = (forecast_time - now_jst).total_seconds()
        if diff >= 0 and diff < min_diff:
            min_diff = diff
            closest = item
    
    # 現在時刻以降のデータがない場合は、最初のアイテムを使用
    if closest is None:
        closest = data["list"][0]
    
    pop = int(closest.get("pop", 0) * 100)
    return pop, closest


def _enrich_snow_from_forecast_item(w: WeatherResult, item: Optional[dict]) -> None:
    if not item:
        return
    #snow volume
    snow = item.get("snow", {})
    snow3h = snow.get("3h")
    if snow3h is not None:
        w.snow_volume_mm_3h = float(snow3h)

    #weather idによる判定
    wid = None
    try:
        if "weather" in item and item.get("weather") and len(item["weather"]) > 0:
            wid = int(item["weather"][0]["id"])
    except (KeyError, IndexError, ValueError, TypeError):
        pass

    pop = int(item.get("pop", 0) * 100)

    if wid is not None and 600 <= wid <= 622:
        w.snow_probability = pop
        return

    #snow量があるなら雪確率は高い
    if w.snow_volume_mm_3h is not None and w.snow_volume_mm_3h > 0:
        w.snow_probability = pop