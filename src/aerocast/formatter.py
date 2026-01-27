import json
from dataclasses import asdict

from openai import OpenAI
from .models import WeatherContext
from .fallback_formatter import simple_format
from .logger import logger
from .validators import validate_llm_output

client = OpenAI()

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
        # LLM 障害時フォールバック（エラーは内部ログのみに記録）
        logger.warning(
            f"LLM API呼び出しに失敗しました: {type(e).__name__}: {e}",
            exc_info=True
        )
        # フォールバックフォーマッターを使用（ユーザーにはエラーを表示しない）
        return simple_format(context)
