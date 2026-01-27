import pytest
from aerocast.snow_estimator import estimate_snow_probability


class TestEstimateSnowProbability:
    """雪確率推定モデルのテスト"""

    def test_zero_rain_probability(self):
        """降水確率が0の場合"""
        assert estimate_snow_probability(0, -5.0) == 0
        assert estimate_snow_probability(0, 5.0) == 0

    def test_negative_temperature(self):
        """気温が0℃以下の場合（雪確率 = 降水確率）"""
        assert estimate_snow_probability(100, -5.0) == 100
        assert estimate_snow_probability(80, 0.0) == 80
        assert estimate_snow_probability(50, -1.0) == 50

    def test_cold_temperature_range(self):
        """0℃ < 気温 < 2℃の場合（雪確率 = 降水確率 * 0.7）"""
        assert estimate_snow_probability(100, 0.1) == 70
        assert estimate_snow_probability(100, 1.0) == 70
        assert estimate_snow_probability(100, 1.9) == 70
        assert estimate_snow_probability(50, 1.5) == 35

    def test_moderate_temperature_range(self):
        """2℃ <= 気温 < 4℃の場合（雪確率 = 降水確率 * 0.3）"""
        assert estimate_snow_probability(100, 2.0) == 30
        assert estimate_snow_probability(100, 3.0) == 30
        assert estimate_snow_probability(100, 3.9) == 30
        assert estimate_snow_probability(80, 2.5) == 24

    def test_warm_temperature(self):
        """気温 >= 4℃の場合（雪確率 = 0%）"""
        assert estimate_snow_probability(100, 4.0) == 0
        assert estimate_snow_probability(100, 10.0) == 0
        assert estimate_snow_probability(100, 25.0) == 0

    def test_edge_cases(self):
        """境界値のテスト"""
        # 0℃ちょうど
        assert estimate_snow_probability(100, 0.0) == 100
        # 2℃ちょうど
        assert estimate_snow_probability(100, 2.0) == 30
        # 4℃ちょうど
        assert estimate_snow_probability(100, 4.0) == 0
