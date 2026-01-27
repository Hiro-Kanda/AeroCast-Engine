"""
バリデーション関数群
"""


class LLMOutputValidation(Exception):
    """LLM出力のバリデーションエラー"""
    pass


def validate_city(city: str) -> bool:
    """都市名のバリデーション"""
    return bool(city and city.strip())


def validate_days(days: int) -> bool:
    """日数のバリデーション（0-5の範囲）"""
    return isinstance(days, int) and 0 <= days <= 5


def validate_llm_output(text: str) -> None:
    """
    LLM出力をバリデーションする。
    判断・推測・推奨を含むテキストを検出する。
    
    Args:
        text: バリデーション対象のテキスト
        
    Raises:
        LLMOutputValidation: 禁止された表現が含まれている場合
    """
    # 禁止ワード・フレーズ（判断・推測・推奨を表す表現）
    forbidden_patterns = [
        "お勧め",
        "おすすめ",
        "推奨",
        "勧め",
        "すべき",
        "した方が",
        "したほうが",
        "すべきです",
        "した方がいい",
        "したほうがいい",
        "した方が良い",
        "したほうが良い",
        "した方がよい",
        "したほうがよい",
        "することをお勧め",
        "することをおすすめ",
        "することを推奨",
        "判断",
        "推測",
        "思います",
        "思われます",
        "かもしれません",
        "でしょう",
        "だと思います",
        "だと思われます",
    ]
    
    text_lower = text.lower()
    for pattern in forbidden_patterns:
        if pattern in text_lower:
            raise LLMOutputValidation(
                f"LLM出力に禁止された表現が含まれています: '{pattern}'"
            )
