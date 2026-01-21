from dataclasses import dataclass
from typing import Literal, Optional


# ===============================
# Fact Model
# ===============================

@dataclass
class WeatherResult:
    city: str
    weather: str
    temp: float
    feels_like: float
    humidity: int
    rain_probability: int # %
    wind_speed: float # m/s
    type: Literal["current", "forecast"]
    date: Optional[str] = None


# ===============================
# Decision Models
# ===============================

@dataclass
class UmbrellaDecision:
    needed: bool
    rain_code: Literal[
        "RAIN_PROB_GE_40",
        "RAIN_PROB_LT_40",
        "NO_RAIN",
    ]


@dataclass
class WindDecision:
    alert: bool
    wind_speed: float
    reason_code: Literal[
        "WIND_GE_10",
        "WIND_LT_10",
    ]


@dataclass
class ComfortDecision:
    level: Literal["HOT", "WARM", "COOL", "COLD"]
    feels_like: float
    reason_code: Literal["FEELS_LIKE_TEMP"]


# ===============================
# Context Model
# ===============================

@dataclass
class WeatherContext:
    weather: WeatherResult
    umbrella: UmbrellaDecision
    wind: WindDecision
    comfort: ComfortDecision