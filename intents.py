from dataclasses import dataclass
from enum import Enum

class IntentType(Enum):
    WEATHER = "weather"
    CHAT = "chat"

@dataclass
class WeatherIntent:
    city: str
    days: int