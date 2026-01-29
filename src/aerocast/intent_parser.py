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
    "おしえて",
    "おしえてください",
    "ください",
    "下さい",
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

def parse_weather_intent(
    text: str,
    context_city: Optional[str] = None,
    context_days: Optional[int] = None
) -> Optional[WeatherIntent]:
    """
    天気意図を解析
    
    Args:
        text: ユーザー入力
        context_city: 前回の会話から引き継ぐ都市名
        context_days: 前回の会話から引き継ぐ日数
    """
    text = text.strip()

    # --- 天気関連トリガー判定（緩和） ---
    # 文脈がある場合はトリガーワードがなくてもOK（「明日は？」など）
    has_trigger = any(w in text for w in TRIGGER_WORDS)
    if not has_trigger and context_city is None:
        return None

    # --- 日数判定 ---
    days = _extract_days(text)
    if days is None:
        # 文脈から日数を引き継ぐ
        if context_days is not None:
            days = context_days
        else:
            days = 0  # デフォルトは今日
    elif not (0 <= days <= 5):
        return None

    # --- 都市名抽出 ---
    city = _extract_city(text)
    if not city:
        # 文脈から都市名を引き継ぐ
        if context_city:
            city = context_city
        else:
            return None

    return WeatherIntent(city=city, days=days)


# ===============================
# Days Extraction
# ===============================

def _extract_days(text: str) -> Optional[int]:
    """日数を抽出（「週末」などの表現にも対応）"""
    if "今日" in text:
        return 0
    if "明日" in text or "あした" in text:
        return 1
    if "明後日" in text or "あさって" in text:
        return 2
    if "明々後日" in text:
        return 3
    
    # 「週末」の処理（土曜日を基準に計算）
    if "週末" in text or "しゅうまつ" in text:
        # 簡易実装：今日から最も近い土曜日までの日数を返す
        # より正確には、現在の曜日を考慮する必要がある
        from datetime import datetime
        today = datetime.now()
        weekday = today.weekday()  # 0=月曜日, 6=日曜日
        # 土曜日までの日数（5=土曜日）
        days_to_saturday = (5 - weekday) % 7
        if days_to_saturday == 0 and weekday != 5:
            days_to_saturday = 7  # 今日が土曜日でない場合、来週の土曜日
        return min(days_to_saturday, 5)  # 最大5日後まで

    # 「◯日後」形式
    m = re.search(r"(\d+)日後", text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None

    # 明示がない場合はNoneを返す（文脈から引き継ぐ）
    return None


# ===============================
# City Extraction
# ===============================

def _extract_city(text: str) -> Optional[str]:
    city = text

    # 時間表現削除（「◯日後」形式も含む）
    for w in TIME_WORDS:
        city = city.replace(w, "")
    
    # 「◯日後」形式を削除（例：「5日後」「3日後」）
    city = re.sub(r"\d+日後", "", city)

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
