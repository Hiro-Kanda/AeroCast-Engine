"""
生活アドバイス生成。

役割:
- 服装提案
- 傘提案
- 風の注意
- 体感コメント
- 季節コメント
"""
from .models import WeatherResult, AdviceResult
from .rules import decide_umbrella, decide_wind, decide_comfort


def _clothing_advice(level: str) -> str:
    """快適度から服装提案"""
    advice = {
        "HOT": "吸汗・速乾の服がおすすめです。日差し対策を。",
        "WARM": "長袖または半袖で過ごせます。",
        "COOL": "長袖・薄手の上着があると安心です。",
        "COLD": "コートやジャケット、暖かい服装で。",
    }
    return advice.get(level, "気温に合わせて調節してください。")


def _umbrella_advice(needed: bool, rain_prob: int) -> str:
    """傘提案"""
    if needed:
        return f"降水確率{rain_prob}%のため、折りたたみ傘があると安心です。"
    if rain_prob > 0:
        return "傘は必須ではありませんが、にわか雨に備えてあると便利です。"
    return "傘は不要です。"


def _wind_advice(alert: bool, wind_speed: float) -> str:
    """風の注意"""
    if alert:
        return f"風が強いです（約{wind_speed:.0f}m/s）。帽子や飛ばされやすいものに注意。"
    return "特段の風の注意は不要です。"


def _feels_like_comment(level: str, feels_like: float) -> str:
    """体感コメント"""
    comments = {
        "HOT": "体感は暑く感じます。",
        "WARM": "体感は過ごしやすいです。",
        "COOL": "体感はやや涼しめです。",
        "COLD": "体感は寒く感じます。",
    }
    return comments.get(level, f"体感は約{feels_like:.0f}℃程度です。")


def _seasonal_comment(month: int, temp: float) -> str:
    """季節コメント（簡易）"""
    if month in (3, 4, 5):
        if temp < 10:
            return "春先は朝晩の冷え込みに注意。"
        if temp < 20:
            return "春らしい気温です。"
        return "日中は暖かく過ごせそうです。"
    if month in (6, 7, 8):
        return "暑さ対策と水分補給を心がけて。"
    if month in (9, 10, 11):
        if temp < 15:
            return "秋の冷え込みが感じられます。"
        return "秋らしい過ごしやすい気温です。"
    if month in (12, 1, 2):
        return "冬の寒さに備えた服装で。"
    return ""


def build_advice(w: WeatherResult) -> AdviceResult:
    """
    WeatherResult から生活アドバイスを生成する。
    """
    from datetime import datetime, timezone, timedelta
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)

    umbrella = decide_umbrella(w)
    wind = decide_wind(w)
    comfort = decide_comfort(w)

    return AdviceResult(
        clothing=_clothing_advice(comfort.level),
        umbrella=_umbrella_advice(umbrella.needed, w.rain_probability),
        wind=_wind_advice(wind.alert, w.wind_speed),
        feels_like_comment=_feels_like_comment(comfort.level, w.feels_like),
        seasonal_comment=_seasonal_comment(now.month, w.temp),
    )
