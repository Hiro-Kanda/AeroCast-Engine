import sys
from pathlib import Path

# pytest実行時に src/ 配下のパッケージを解決できるようにする
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest
from unittest.mock import Mock, patch
from aerocast.models import WeatherResult


@pytest.fixture
def sample_weather_result():
    """テスト用のWeatherResultフィクスチャ"""
    return WeatherResult(
        city="東京",
        weather="晴れ",
        temp=25.0,
        feels_like=26.0,
        humidity=60,
        rain_probability=30,
        wind_speed=5.0,
        type="current",
    )
