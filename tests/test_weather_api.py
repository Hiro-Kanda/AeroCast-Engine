import pytest
from unittest.mock import Mock, patch
from aerocast.weather_api import resolve_city, fetch_weather, fetch_current_weather
from aerocast.error import CityNotFoundError, WeatherAPIError


class TestResolveCity:
    """地名解決のテスト"""

    @patch("aerocast.weather_api._SESSION")
    def test_resolve_city_success(self, mock_session):
        """正常な地名解決"""
        mock_response = Mock()
        mock_response.json.return_value = [{"lat": 35.6762, "lon": 139.6503}]
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        lat, lon = resolve_city("東京")
        assert lat == 35.6762
        assert lon == 139.6503

    @patch("aerocast.weather_api._SESSION")
    def test_resolve_city_not_found(self, mock_session):
        """存在しない地名"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        with pytest.raises(CityNotFoundError):
            resolve_city("存在しない都市")

    @patch("aerocast.weather_api._SESSION")
    def test_resolve_city_api_error(self, mock_session):
        """API接続エラー"""
        mock_session.get.side_effect = Exception("Connection error")

        with pytest.raises(WeatherAPIError):
            resolve_city("東京")


class TestFetchWeather:
    """天気取得のテスト"""

    @patch("aerocast.weather_api.fetch_current_weather")
    @patch("aerocast.weather_api.resolve_city")
    def test_fetch_weather_current(self, mock_resolve, mock_fetch):
        """現在の天気取得"""
        mock_resolve.return_value = (35.6762, 139.6503)
        mock_result = Mock()
        mock_fetch.return_value = mock_result

        result = fetch_weather("東京", 0)
        assert result == mock_result
        mock_fetch.assert_called_once_with("東京", 35.6762, 139.6503)

    @patch("aerocast.weather_api.fetch_forecast_weather")
    @patch("aerocast.weather_api.resolve_city")
    def test_fetch_weather_forecast(self, mock_resolve, mock_fetch):
        """予報取得"""
        mock_resolve.return_value = (35.6762, 139.6503)
        mock_result = Mock()
        mock_fetch.return_value = mock_result

        result = fetch_weather("東京", 1)
        assert result == mock_result
        mock_fetch.assert_called_once_with("東京", 35.6762, 139.6503, 1)
