from typing import Optional
from .state import AgentState
from .actions import Action
from .intent_parser import parse_weather_intent
from .validators import validate_days
from .weather_api import fetch_weather
from .rules import decide_umbrella, decide_wind, decide_comfort
from .formatter import format_weather
from .models import WeatherContext, WeatherResult
from .error import UserFacingError, CityNotFoundError, AmbiguousCityError
from .session import get_session_context

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

def run(user_input: str, session_id: str = "default", max_steps: int = 10) -> str:
  """
  エージェントを実行
  
  Args:
    user_input: ユーザー入力
    session_id: セッションID（会話の文脈を保持するため）
    max_steps: 最大ステップ数
  """
  # セッションから文脈を取得
  context = get_session_context(session_id)
  
  s = AgentState(user_input=user_input)

  for _ in range(max_steps):
    a = next_action(s)
    s.steps.append(a.value)

    if a == Action.PARSE_INTENT:
      # 文脈を考慮して意図を解析
      intent = parse_weather_intent(
        s.user_input,
        context_city=context.last_city,
        context_days=context.last_days
      )
      if intent is None:
        return "天気に関する質問のみ対応しています。"
      s.city = intent.city
      s.days = intent.days
      s.intent = "forecast"  # 意図を文字列で保存
      
      # 文脈を更新
      context.update(city=s.city, days=s.days, intent=s.intent)
      
      if not s.city:
        s.need_clarification = True
        s.clarification_question = "都市名を教えてください。"
        return s.clarification_question
      continue

    if a == Action.VALIDATE:
      if s.days is None:
        return "日数が指定されていません。"
      if not validate_days(s.days):
        return f"日数は0〜5の範囲で指定してください。現在の値: {s.days}"
      # バリデーション成功後は次のアクションへ
      continue

    if a == Action.FETCH_WEATHER:
      try:
        # fetch_weather内でresolve_city_with_candidatesが呼ばれる（リトライ機能付き）
        # 都市名が曖昧な場合はCityNotFoundErrorに候補が含まれる
        weather = fetch_weather(s.city, s.days)
        s.weather = weather
      except AmbiguousCityError as e:
        return str(e)
      except CityNotFoundError as e:
        # 都市名が曖昧な場合、候補を提示
        return str(e)
      except UserFacingError as e:
        return str(e)
      except Exception as e:
        return f"天気情報の取得に失敗しました: {e}"
      continue

    if a == Action.FORMAT:
      if s.weather is None:
        return "天気情報が取得できませんでした。"
      # WeatherResultからWeatherContextを生成
      weather_result: WeatherResult = s.weather
      context_weather = WeatherContext(
        weather=weather_result,
        umbrella=decide_umbrella(weather_result),
        wind=decide_wind(weather_result),
        comfort=decide_comfort(weather_result),
      )
      result = format_weather(context_weather)
      # 成功したら文脈を更新
      context.update(city=s.city, days=s.days, intent=s.intent)
      return result

    if a == Action.ASK_CLARIFICATION:
      if s.clarification_question:
        return s.clarification_question
      return "都市名を教えてください。"

  return "うまく処理できませんでした。都市名と日付を指定してください。"