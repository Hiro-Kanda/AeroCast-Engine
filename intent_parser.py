from dataclasses import dataclass
from random import expovariate

@dataclass
class WeatherIntent:
    city: str
    days: int #0~7


def parse_weather_intent(text: str) -> WeatherIntent | None:
    if "天気" not in text:
        return None

    # 時間表現を除外するリスト
    time_expressions = ["今日", "明日", "明後日", "あさって", "昨日", "一昨日"]
    
    # 日数の判定
    days = 0
    if "今日" in text:
        days = 0
    elif "明日" in text or "あした" in text:
        days = 1
    elif "明後日" in text or "あさって" in text:
        days = 2
    elif "日後" in text:
        try:
            days = int(text.split("日後")[0][-1])
        except ValueError:
            days = 0
    
    # 「の天気」の前の部分から都市名を抽出
    if "の天気" in text:
        before_weather = text.split("の天気")[0]
    else:
        before_weather = text.split("天気")[0]
    
    # 「の」で分割して、時間表現を除外
    parts = before_weather.split("の")
    city = None
    
    # 後ろから見て、時間表現でない最初の部分を都市名とする
    for part in reversed(parts):
        part = part.strip()
        if part and part not in time_expressions:
            city = part
            break
    
    # 都市名が見つからない場合、最後の部分を使用
    if not city and parts:
        city = parts[-1].strip()
    
    # まだ見つからない場合、全体を使用
    if not city:
        city = before_weather.strip()
    
    # 時間表現のみの場合はエラー
    if city in time_expressions:
        return None
    
    # 余分な文字を削除
    city = city.strip()
    
    # 空の場合はエラー
    if not city:
        return None

    if not (0 <= days <= 7):
        return None
    return WeatherIntent(city=city, days=days)
