"""
バリデーション関数群
"""

def validate_city(city: str) -> bool:
    """都市名のバリデーション"""
    return bool(city and city.strip())


def validate_days(days: int) -> bool:
    """日数のバリデーション（0-5の範囲）"""
    return isinstance(days, int) and 0 <= days <= 5
