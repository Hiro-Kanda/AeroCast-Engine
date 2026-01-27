import pytest
from aerocast.rules import (
    decide_umbrella,
    decide_wind,
    decide_comfort,
    RAIN_UMBRELLA_THRESHOLD,
    WIND_ALERT_THRESHOLD,
)
from aerocast.models import WeatherResult


class TestDecideUmbrella:
    """傘の判断テスト"""

    def test_umbrella_needed_high_rain_probability(self):
        """降水確率が高い場合"""
        weather = WeatherResult(
            city="東京",
            weather="雨",
            temp=20.0,
            feels_like=20.0,
            humidity=80,
            rain_probability=RAIN_UMBRELLA_THRESHOLD,
            wind_speed=5.0,
            type="current",
        )
        decision = decide_umbrella(weather)
        assert decision.needed is True
        assert decision.rain_code == "RAIN_PROB_GE_40"

    def test_umbrella_not_needed_low_rain_probability(self):
        """降水確率が低い場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=25.0,
            feels_like=25.0,
            humidity=60,
            rain_probability=RAIN_UMBRELLA_THRESHOLD - 1,
            wind_speed=3.0,
            type="current",
        )
        decision = decide_umbrella(weather)
        assert decision.needed is False
        assert decision.rain_code == "RAIN_PROB_LT_40"


class TestDecideWind:
    """風速の判断テスト"""

    def test_wind_alert_high_speed(self):
        """風速が高い場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=20.0,
            feels_like=20.0,
            humidity=60,
            rain_probability=0,
            wind_speed=WIND_ALERT_THRESHOLD,
            type="current",
        )
        decision = decide_wind(weather)
        assert decision.alert is True
        assert decision.wind_speed == WIND_ALERT_THRESHOLD
        assert decision.reason_code == "WIND_GE_10"

    def test_wind_no_alert_low_speed(self):
        """風速が低い場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=20.0,
            feels_like=20.0,
            humidity=60,
            rain_probability=0,
            wind_speed=WIND_ALERT_THRESHOLD - 1,
            type="current",
        )
        decision = decide_wind(weather)
        assert decision.alert is False
        assert decision.reason_code == "WIND_LT_10"


class TestDecideComfort:
    """快適度の判断テスト"""

    def test_comfort_hot(self):
        """暑い場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=30.0,
            feels_like=30.0,
            humidity=60,
            rain_probability=0,
            wind_speed=2.0,
            type="current",
        )
        decision = decide_comfort(weather)
        assert decision.level == "HOT"

    def test_comfort_warm(self):
        """暖かい場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=25.0,
            feels_like=25.0,
            humidity=60,
            rain_probability=0,
            wind_speed=2.0,
            type="current",
        )
        decision = decide_comfort(weather)
        assert decision.level == "WARM"

    def test_comfort_cool(self):
        """涼しい場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=15.0,
            feels_like=15.0,
            humidity=60,
            rain_probability=0,
            wind_speed=2.0,
            type="current",
        )
        decision = decide_comfort(weather)
        assert decision.level == "COOL"

    def test_comfort_cold(self):
        """寒い場合"""
        weather = WeatherResult(
            city="東京",
            weather="晴れ",
            temp=5.0,
            feels_like=5.0,
            humidity=60,
            rain_probability=0,
            wind_speed=2.0,
            type="current",
        )
        decision = decide_comfort(weather)
        assert decision.level == "COLD"
