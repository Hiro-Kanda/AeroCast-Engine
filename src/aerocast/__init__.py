"""
AeroCast Engine Package

天気情報を取得し、データ化、予測の回答を行うパッケージ
"""

# メインのエージェント関数
from .agent import run_agent

# データモデル
from .models import (
    WeatherContext,
    WeatherResult,
    UmbrellaDecision,
    WindDecision,
    ComfortDecision,
)

# エラークラス
from .error import (
    UserFacingError,
    CityNotFoundError,
    WeatherAPIError,
)

# 公開APIを明示的に定義
__all__ = [
    # メイン関数
    "run_agent",
    # データモデル
    "WeatherContext",
    "WeatherResult",
    "UmbrellaDecision",
    "WindDecision",
    "ComfortDecision",
    # エラークラス
    "UserFacingError",
    "CityNotFoundError",
    "WeatherAPIError",
]
