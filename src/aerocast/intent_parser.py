import re
from dataclasses import dataclass
from typing import Optional


# ===============================
# Intent Model
# ===============================

@dataclass
class WeatherIntent:
    city: str
    days: int  # 0〜5


# ===============================
# Trigger / Noise Words
# ===============================

TRIGGER_WORDS = [
    "天気",
    "予報",
    "雨",
    "気温",
    "暑い",
    "寒い",
]

NOISE_WORDS = [
    "の",
    "を",
    "について",
    "教えて",
    "教えてください",
    "ください",
    "知りたい",
    "は",
    "って",
]

TIME_WORDS = [
    "今日",
    "明日",
    "明後日",
    "明々後日",
]


# ===============================
# Main Parser
# ===============================

def parse_weather_intent(text: str) -> Optional[WeatherIntent]:
    text = text.strip()

    # --- 天気関連トリガー判定（緩和） ---
    if not any(w in text for w in TRIGGER_WORDS):
        return None

    # --- 日数判定 ---
    days = _extract_days(text)
    if days is None or not (0 <= days <= 5):
        return None

    # --- 都市名抽出 ---
    city = _extract_city(text)
    if not city:
        return None

    return WeatherIntent(city=city, days=days)


# ===============================
# Days Extraction
# ===============================

def _extract_days(text: str) -> Optional[int]:
    if "今日" in text:
        return 0
    if "明日" in text or "あした" in text:
        return 1
    if "明後日" in text or "あさって" in text:
        return 2
    if "明々後日" in text:
        return 3

    # 「◯日後」形式
    m = re.search(r"(\d+)日後", text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None

    # 明示がない場合は「今日」扱い
    return 0


# ===============================
# City Extraction
# ===============================

def _extract_city(text: str) -> Optional[str]:
    city = text

    # 時間表現削除
    for w in TIME_WORDS:
        city = city.replace(w, "")

    # トリガーワード削除
    for w in TRIGGER_WORDS:
        city = city.replace(w, "")

    # ノイズ削除
    for w in NOISE_WORDS:
        city = city.replace(w, "")

    # 記号・余分な空白削除
    city = re.sub(r"[?？!！。、]", "", city)
    city = re.sub(r"\s+", "", city)

    city = city.strip()
    # 空文字列の場合はNoneを返す
    return city if city else None
