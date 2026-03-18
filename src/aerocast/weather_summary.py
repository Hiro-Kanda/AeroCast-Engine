"""
APIレスポンスを表示向けに要約する。

役割:
- condition_text を作る
- max/min 気温を抽出
- 降水量や降水確率を要約
- 日付ラベルを作る
"""
from datetime import datetime, timezone, timedelta

from .models import WeatherResult, WeatherSummary

JST = timezone(timedelta(hours=9))


def _build_date_label(w: WeatherResult, days_offset: int = 0) -> str:
    """日付ラベルを生成（今日・明日・○月○日など）"""
    if w.date:
        return w.date
    if w.type == "current" or days_offset == 0:
        return "今日"
    if days_offset == 1:
        return "明日"
    if days_offset == 2:
        return "明後日"
    if 0 <= days_offset <= 5:
        target = datetime.now(JST).date() + timedelta(days=days_offset)
        return f"{target.month}月{target.day}日頃"
    return "予報日"


def _build_precipitation_summary(w: WeatherResult) -> str:
    """降水量・降水確率を要約した文言"""
    parts = []
    if w.rain_probability is not None and w.rain_probability > 0:
        parts.append(f"降水確率{w.rain_probability}%")
    if w.snow_probability is not None and w.snow_probability > 0:
        parts.append(f"雪の可能性{w.snow_probability}%")
    if w.snow_volume_mm_3h is not None and w.snow_volume_mm_3h > 0:
        parts.append(f"積雪量（3時間）約{w.snow_volume_mm_3h:.0f}mm")
    if not parts:
        return "降水・降雪の可能性は低いです。"
    return "。".join(parts) + "。"


def build_summary(w: WeatherResult, days_offset: int = 0) -> WeatherSummary:
    """
    WeatherResult から表示向け要約を生成する。

    Args:
        w: 天気API取得結果
        days_offset: 0=今日, 1=明日, ...
    """
    condition_text = w.weather or "—"
    temp = w.temp
    temp_max = temp
    temp_min = temp
    # 現在APIは1時点のみのため max/min は同じ。将来複数時点があれば集約可能

    return WeatherSummary(
        city=w.city,
        condition_text=condition_text,
        temp_max=temp_max,
        temp_min=temp_min,
        precipitation_summary=_build_precipitation_summary(w),
        date_label=_build_date_label(w, days_offset),
        observed_at_jst=w.observed_at_jst,
    )
