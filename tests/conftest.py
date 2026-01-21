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
