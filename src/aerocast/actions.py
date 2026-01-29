from enum import Enum

class Action(str, Enum):
  PARSE_INTENT = "parse_intent"
  VALIDATE = "validate"
  RESOLVE_CITY = "resolve_city"
  FETCH_WEATHER = "fetch_weather"
  DECIDE = "decide"
  FORMAT = "format"
  ASK_CLARIFICATION = "ask_clarification"
  DONE = "done"