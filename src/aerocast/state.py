from dataclasses import dataclass, field
from typing import List, Optional

from .models import WeatherResult

@dataclass
class AgentState:
  user_input: str
  city: Optional[str] = None
  days: Optional[int] = None
  intent: Optional[str] = None  # "forecast" などの文字列
  weather: Optional[WeatherResult] = None

  need_clarification: bool = False
  clarification_question: Optional[str] = None

  errors: List[str] = field(default_factory=list)
  steps: List[str] = field(default_factory=list)