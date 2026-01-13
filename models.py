from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class WeatherResult:
    city: str
    weather: str
    temp: float
    type: Literal["current", "forecast"]
    date: Optional[str] = None