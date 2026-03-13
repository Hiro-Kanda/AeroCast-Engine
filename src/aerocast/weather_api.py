import os
import requests
from datetime import datetime, timedelta, time, timezone
from typing import Optional, List, Tuple
from urllib.parse import quote

from .models import WeatherResult
from .error import CityNotFoundError, WeatherAPIError, AmbiguousCityError
from .logger import logger
from .snow_estimator import estimate_snow_probability
from .retry import exponential_backoff

def _get_openweather_key() -> str:
    """
    APIキーは import 時ではなく、実際にAPIを叩く直前に検証する。
    （pytest/静的解析/一部環境での import 失敗を防ぐ）
    """
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise WeatherAPIError("OPENWEATHER_API_KEY が設定されていません")
    return key

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
    key = _get_openweather_key()
    encoded_city = quote(city_variant)
    url = (
        "https://api.openweathermap.org/geo/1.0/direct"
        f"?q={encoded_city},JP&limit={limit}&appid={key}"
    )
    response = _SESSION.get(url, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _format_geo_candidate(item: dict) -> str:
    """geo/1.0/direct の候補表示用文字列を作る"""
    name = item.get("name", "")
    state = item.get("state")
    country = item.get("country")
    if state:
        return f"{name}（{state}）"
    if country:
        return f"{name}（{country}）"
    return name or "不明"


# 複数候補が返っても「先頭を採用してよい」代表的な都市名（都道府県・主要都市）
# OpenWeatherMap が複数件返す場合でも、ユーザーが意図するのは通常この1件
WELL_KNOWN_CITY_NAMES = frozenset({
    "東京", "大阪", "名古屋", "横浜", "福岡", "札幌", "京都", "神戸", "川崎", "さいたま",
    "広島", "仙台", "北九州", "熊本", "岡山", "静岡", "新潟", "長崎", "岐阜", "奈良", "長野",
    "千葉", "堺", "富山", "金沢", "高松", "松山", "那覇", "宇都宮", "前橋", "水戸", "盛岡",
    "秋田", "山形", "福島", "郡山", "いわき", "青森", "弘前", "函館", "小樽", "旭川", "帯広",
    "釧路", "室蘭", "苫小牧", "江別", "北広島", "石巻", "気仙沼", "多賀城", "岩沼", "登米",
    "大崎", "古川", "角田", "白石", "柴田", "伊達", "仙台", "山形", "米沢", "鶴岡", "酒田",
    "新庄", "寒河江", "上山市", "天童", "東根", "尾花沢", "南陽", "長井", "福島", "いわき",
    "郡山", "会津若松", "白河", "須賀川", "二本松", "田村", "南相馬", "本宮", "喜多方",
})


def _first_result_matches_query(city_variant: str, first_item: dict) -> bool:
    """先頭候補がユーザー入力と同一の場所を指すとみなせるか"""
    name = (first_item.get("name") or "").strip()
    local_names = first_item.get("local_names") or {}
    local_ja = (local_names.get("ja") or "").strip()
    q = (city_variant or "").strip()
    if not q:
        return False
    if name == q or local_ja == q:
        return True
    if q in WELL_KNOWN_CITY_NAMES:
        return True
    return False


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
                # 候補を整形して収集（重複排除）
                candidates = []
                for item in data:
                    cand = _format_geo_candidate(item)
                    if cand and cand not in candidates:
                        candidates.append(cand)

                # 複数候補が返った場合：先頭がユーザー入力と一致するなら先頭を採用（東京・大阪などで正しく解釈）
                # 一致しない場合のみ「曖昧」として候補を返す
                if limit > 1 and len(candidates) > 1:
                    if _first_result_matches_query(city_variant, data[0]):
                        lat, lon = data[0]["lat"], data[0]["lon"]
                        return (lat, lon), []
                    return None, candidates

                # 単一候補（またはlimit==1）は先頭を採用
                lat, lon = data[0]["lat"], data[0]["lon"]
                return (lat, lon), []
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
    key = _get_openweather_key()
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={key}&units=metric&lang=ja"
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
    key = _get_openweather_key()

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&cnt=40"
        f"&appid={key}&units=metric&lang=ja"
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

    same_day_items = []

    closest = None
    min_diff = float("inf")

    for item in data["list"]:
        forecast_time = datetime.fromtimestamp(
            item["dt"],
            tz=timezone.utc,
        ).astimezone(JST)
        if forecast_time.date() != target_date:
            continue
        same_day_items.append((forecast_time, item))

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
    coords, candidates = resolve_city_with_candidates(city, limit=5)

    # 候補が1件でもあれば勝手に確定せず、ユーザーに聞き返す（候補提示を確実に発火）
    if candidates:
        raise AmbiguousCityError(city, candidates)

    if coords is None:
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
    key = _get_openweather_key()
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&cnt=40"
        f"&appid={key}&units=metric&lang=ja"
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
