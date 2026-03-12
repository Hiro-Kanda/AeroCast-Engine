"""
最終的なMarkdown整形。

役割:
- セクション見出し生成
- bulletの整形
- 余計な重複排除
"""
import json
from dataclasses import asdict

from openai import OpenAI
from .models import WeatherContext, WeatherSummary, AdviceResult
from .fallback_formatter import simple_format
from .logger import logger
from .validators import validate_llm_output

_client = None


def _dedup_lines(lines: list[str]) -> list[str]:
    """重複を排除（同一・類似の連続を1つに）"""
    seen = set()
    result = []
    for s in lines:
        n = s.strip()
        if not n or n in seen:
            continue
        seen.add(n)
        result.append(s)
    return result


def format_to_markdown(summary: WeatherSummary, advice: AdviceResult) -> str:
    """
    WeatherSummary と AdviceResult から Markdown テキストを生成する。
    セクション見出し・bullet 整形・重複排除を行う。
    """
    lines = []

    # セクション: 天気の目安
    lines.append(f"## {summary.city}（{summary.date_label}）の天気の目安")
    lines.append("")
    bullets = [
        f"- 天気: {summary.condition_text}",
        f"- 気温: 約{summary.temp_min:.0f}～{summary.temp_max:.0f}℃",
        f"- 降水: {summary.precipitation_summary}",
    ]
    if summary.observed_at_jst:
        bullets.append(f"- 基準時刻: {summary.observed_at_jst}")
    lines.extend(_dedup_lines(bullets))
    lines.append("")

    # セクション: 体感のポイント
    lines.append("## 体感のポイント")
    lines.append("")
    advice_bullets = [
        f"- {advice.feels_like_comment}",
        f"- {advice.clothing}",
    ]
    if advice.seasonal_comment:
        advice_bullets.append(f"- {advice.seasonal_comment}")
    lines.extend(_dedup_lines(advice_bullets))
    lines.append("")

    # セクション: 持ち物・注意
    lines.append("## 持ち物・注意")
    lines.append("")
    lines.append(f"- {advice.umbrella}")
    lines.append(f"- {advice.wind}")
    lines.append("")

    return "\n".join(lines).strip()


def _get_client() -> OpenAI:
    """APIを叩く直前にクライアントを取得（import時にAPIキーを要求しない）"""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client

def format_weather(context: WeatherContext) -> str:
    """
    WeatherContextに含まれる事実データと判断結果を
    自然な日本語で説明する。
    判断・推測は禁止。
    """

    system_prompt = (
        "あなたは天気情報を分かりやすく説明するアシスタントです。"
        "与えられた情報のみを説明してください。新しい判断や推測は行わないでください。"
        "回答には必ずデータの基準時刻(observed_at_jst)を含めてください。"
        "snow_probabilityは推定値の可能性があるため、推定の場合は『推定』と明記してください。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": json.dumps(asdict(context), ensure_ascii=False),
        },
    ]

    try:
        client = _get_client()
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
        output = res.choices[0].message.content
        # LLM出力をバリデーション（判断・推測・推奨を検出）
        validate_llm_output(output)
        return output
    except Exception as e:
        # LLM 障害時フォールバック（エラーは内部ログのみに記録、ユーザーには表示しない）
        logger.debug(
            f"LLM API呼び出しに失敗しました: {type(e).__name__}: {e}",
            exc_info=True
        )
        # フォールバックフォーマッターを使用（ユーザーにはエラーを表示しない）
        return simple_format(context)
