from dataclasses import asdict, dataclass
from typing import Optional, Any

from .state import AgentState
from .actions import Action
from .intent_parser import parse_weather_intent
from .validators import validate_days
from .weather_api import fetch_weather
from .rules import decide_umbrella, decide_wind, decide_comfort
from .formatter import format_to_markdown
from .weather_summary import build_summary
from .advice_engine import build_advice
from .models import WeatherResult
from .error import UserFacingError, CityNotFoundError, AmbiguousCityError
from .session import get_session_context
from .preprocessor import normalize_user_input


@dataclass
class RunResult:
    """エージェント実行結果（API用・優先度3: レスポンス構造化）"""
    reply: str
    location: Optional[str] = None
    forecast: Optional[dict] = None  # API取得値 (WeatherResult)
    judgement: Optional[dict] = None  # 内部判定 (umbrella, wind, comfort)


def next_action(s: AgentState) -> Action:
  if s.intent is None or s.days is None:
    return Action.PARSE_INTENT
  if s.days is not None and not validate_days(s.days):
    return Action.VALIDATE
  if s.city is None:
    return Action.ASK_CLARIFICATION
  # 都市名があるが、まだ解決していない可能性がある場合はRESOLVE_CITY
  # （実際にはfetch_weather内で解決されるが、候補を取得する場合はここで処理）
  if s.weather is None:
    return Action.FETCH_WEATHER
  return Action.FORMAT

def _run_inner(
  user_input: str, session_id: str = "default", max_steps: int = 10
) -> RunResult:
  """
  エージェントを実行し、構造化結果を返す（内部用）。
  優先度3: 内部判定・API取得値・LLM整形文を分けて返す。
  """
  context = get_session_context(session_id)
  normalized_input = normalize_user_input(user_input)
  s = AgentState(user_input=normalized_input)

  for _ in range(max_steps):
    a = next_action(s)
    s.steps.append(a.value)

    if a == Action.PARSE_INTENT:
      intent = parse_weather_intent(
        s.user_input,
        context_city=context.last_city,
        context_days=context.last_days
      )
      if intent is None:
        return RunResult(reply="天気に関する質問のみ対応しています。")
      s.city = intent.city
      s.days = intent.days
      s.intent = "forecast"
      context.update(city=s.city, days=s.days, intent=s.intent)
      if not s.city:
        s.need_clarification = True
        s.clarification_question = "都市名を教えてください。"
        return RunResult(reply=s.clarification_question or "都市名を教えてください。")
      continue

    if a == Action.VALIDATE:
      if s.days is None:
        return RunResult(reply="日数が指定されていません。")
      if not validate_days(s.days):
        return RunResult(
          reply=f"日数は0〜5の範囲で指定してください。現在の値: {s.days}"
        )
      continue

    if a == Action.FETCH_WEATHER:
      try:
        weather = fetch_weather(s.city, s.days)
        s.weather = weather
      except AmbiguousCityError as e:
        return RunResult(reply=str(e))
      except CityNotFoundError as e:
        return RunResult(reply=str(e))
      except UserFacingError as e:
        return RunResult(reply=str(e))
      except Exception as e:
        return RunResult(reply=f"天気情報の取得に失敗しました: {e}")
      continue

    if a == Action.FORMAT:
      if s.weather is None:
        return RunResult(reply="天気情報が取得できませんでした。")
      weather_result: WeatherResult = s.weather
      days_offset = s.days if s.days is not None else 0
      summary = build_summary(weather_result, days_offset=days_offset)
      advice = build_advice(weather_result)
      reply = format_to_markdown(summary, advice)
      umbrella = decide_umbrella(weather_result)
      wind = decide_wind(weather_result)
      comfort = decide_comfort(weather_result)
      context.update(city=s.city, days=s.days, intent=s.intent)
      return RunResult(
        reply=reply,
        location=s.city,
        forecast=asdict(weather_result),
        judgement={
          "umbrella": asdict(umbrella),
          "wind": asdict(wind),
          "comfort": asdict(comfort),
        },
      )

    if a == Action.ASK_CLARIFICATION:
      reply = s.clarification_question or "都市名を教えてください。"
      return RunResult(reply=reply)

  return RunResult(reply="うまく処理できませんでした。都市名と日付を指定してください。")


def run(user_input: str, session_id: str = "default", max_steps: int = 10) -> str:
  """
  エージェントを実行（CLI・後方互換）

  Args:
    user_input: ユーザー入力
    session_id: セッションID（会話の文脈を保持するため）
    max_steps: 最大ステップ数
  """
  return _run_inner(user_input, session_id, max_steps).reply


def run_structured(
  user_input: str, session_id: str = "default", max_steps: int = 10
) -> dict[str, Any]:
  """
  エージェントを実行し、API用の構造化レスポンスを返す。
  reply: LLM整形文、forecast: API取得値、judgement: 内部判定結果。
  """
  r = _run_inner(user_input, session_id, max_steps)
  return {
    "reply": r.reply,
    "location": r.location,
    "forecast": r.forecast,
    "judgement": r.judgement,
  }