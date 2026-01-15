from models import (
    WeatherResult,
    UmbrellaDecision,
    WindDecision,
    ComfortDecision,
)

# ===============================
# Constants (Decision Threshholds)
# ===============================

RAIN_UMBRELLA_THRESHOLD = 40 # %
WIND_ALEART_THRESHOLD = 10 # m/s

# ===============================
# Umbrella Decision
# ===============================

def decide_umbrella(weather: WeatherResult) -> UmbrellaDecision:
    """

    傘が必要か降水確率のみで判断する
    推測や補正は行わない
    """
    rp = weather.rain_probability

    if rp >= RAIN_UMBRELLA_THRESHOLD:
        return UmbrellaDecision(
            needed=True,
            rain_code="RAIN_PROB_GE_40",
        )
    
    return UmbrellaDecision(
        needed=False,
        rain_code="RAIN_PROB_LT_40",
    )


# ===============================
# Wind Decision
# ===============================

def decide_wind(weather: WeatherResult) -> WindDecision:
    """

    今日不注意が必要かを風速のみで判断する
    """
    ws = weather.wind_speed
    
    if ws >= WIND_ALEART_THRESHOLD:
        return WindDecision(
            alert=True,
            wind_speed=ws,
            reason_code="WIND_GE_10",
        )
    
    return WindDecision(
        alert=False,
        wind_speed=ws,
        reason_code="WIND_LT_10",
    )


# ===============================
# Comfort Decision
# ===============================

def decide_comfort(weather: WeatherResult) -> ComfortDecision:
    """

    体感温度から快適温を分類
    """
    ft = weather.feels_like
    
    if ft >= 30:
        level = "HOT"
    elif ft >= 20:
        level = "WARM"
    elif ft >= 10:
        level = "COOL"
    else:
        level = "COLD"

    return ComfortDecision(
        level=level,
        feels_like=ft,
        reason_code="FEELS_LIKE_TEMP",
    )