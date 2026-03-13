from datetime import date, datetime, timezone as dt_timezone
from unittest.mock import Mock, patch

import pytest

from aerocast.error import AmbiguousCityError, CityNotFoundError, WeatherAPIError
from aerocast.models import WeatherResult
from aerocast.weather_api import fetch_forecast_weather, fetch_weather, resolve_city


class TestResolveCity:
    @patch("aerocast.weather_api.resolve_city_with_candidates")
    def test_resolve_city_success(self, mock_resolve):
        mock_resolve.return_value = ((35.6762, 139.6503), [])

        lat, lon = resolve_city("Tokyo")

        assert lat == 35.6762
        assert lon == 139.6503
        mock_resolve.assert_called_once_with("Tokyo", limit=1)

    @patch("aerocast.weather_api.resolve_city_with_candidates")
    def test_resolve_city_not_found(self, mock_resolve):
        mock_resolve.return_value = (None, [])

        with pytest.raises(CityNotFoundError):
            resolve_city("MissingCity")


class TestFetchWeather:
    @patch("aerocast.weather_api.fetch_nowcast_probability")
    @patch("aerocast.weather_api.fetch_current_weather")
    @patch("aerocast.weather_api.resolve_city_with_candidates")
    def test_fetch_weather_current(
        self,
        mock_resolve,
        mock_fetch_current,
        mock_nowcast,
    ):
        mock_resolve.return_value = ((35.6762, 139.6503), [])
        mock_result = WeatherResult(
            city="Tokyo",
            weather="clear",
            temp=20.0,
            feels_like=20.0,
            humidity=60,
            rain_probability=0,
            wind_speed=3.0,
            type="current",
        )
        mock_fetch_current.return_value = mock_result
        mock_nowcast.return_value = (55, None)

        result = fetch_weather("Tokyo", 0)

        assert result is mock_result
        assert result.rain_probability == 55
        mock_resolve.assert_called_once_with("Tokyo", limit=5)
        mock_fetch_current.assert_called_once_with("Tokyo", 35.6762, 139.6503)
        mock_nowcast.assert_called_once_with(35.6762, 139.6503)

    @patch("aerocast.weather_api.fetch_forecast_weather")
    @patch("aerocast.weather_api.resolve_city_with_candidates")
    def test_fetch_weather_forecast(self, mock_resolve, mock_fetch_forecast):
        mock_resolve.return_value = ((35.6762, 139.6503), [])
        mock_result = Mock()
        mock_fetch_forecast.return_value = mock_result

        result = fetch_weather("Tokyo", 1)

        assert result == mock_result
        mock_resolve.assert_called_once_with("Tokyo", limit=5)
        mock_fetch_forecast.assert_called_once_with("Tokyo", 35.6762, 139.6503, 1)

    @patch("aerocast.weather_api.resolve_city_with_candidates")
    def test_fetch_weather_ambiguous_city(self, mock_resolve):
        mock_resolve.return_value = (None, ["Tokyo", "Tokyo Station"])

        with pytest.raises(AmbiguousCityError):
            fetch_weather("Tokyo", 0)


class TestFetchForecastWeather:
    @patch("aerocast.weather_api._get_openweather_key", return_value="dummy-key")
    @patch("aerocast.weather_api._SESSION")
    @patch("aerocast.weather_api.datetime")
    def test_fetch_forecast_weather_uses_requested_date_only(
        self,
        mock_datetime,
        mock_session,
        _mock_key,
    ):
        mock_datetime.now.return_value = Mock(date=Mock(return_value=date(2026, 3, 13)))
        mock_datetime.combine.side_effect = datetime.combine
        mock_datetime.fromtimestamp.side_effect = datetime.fromtimestamp

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "list": [
                {
                    "dt": int(datetime(2026, 3, 13, 21, 0, tzinfo=dt_timezone.utc).timestamp()),
                    "weather": [{"description": "day0"}],
                    "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 60},
                    "wind": {"speed": 3.0},
                    "pop": 0.1,
                },
                {
                    "dt": int(datetime(2026, 3, 14, 3, 0, tzinfo=dt_timezone.utc).timestamp()),
                    "weather": [{"description": "target-day"}],
                    "main": {"temp": 12.0, "feels_like": 11.0, "humidity": 55},
                    "wind": {"speed": 4.0},
                    "pop": 0.2,
                },
            ]
        }
        mock_session.get.return_value = response

        result = fetch_forecast_weather("Tokyo", 35.6762, 139.6503, 1)

        assert result.weather == "target-day"
        assert result.temp == 12.0

    @patch("aerocast.weather_api._get_openweather_key", return_value="dummy-key")
    @patch("aerocast.weather_api._SESSION")
    @patch("aerocast.weather_api.datetime")
    def test_fetch_forecast_weather_errors_when_requested_date_missing(
        self,
        mock_datetime,
        mock_session,
        _mock_key,
    ):
        mock_datetime.now.return_value = Mock(date=Mock(return_value=date(2026, 3, 13)))
        mock_datetime.combine.side_effect = datetime.combine
        mock_datetime.fromtimestamp.side_effect = datetime.fromtimestamp

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "list": [
                {
                    "dt": int(datetime(2026, 3, 13, 21, 0, tzinfo=dt_timezone.utc).timestamp()),
                    "weather": [{"description": "day0"}],
                    "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 60},
                    "wind": {"speed": 3.0},
                    "pop": 0.1,
                }
            ]
        }
        mock_session.get.return_value = response

        with pytest.raises(WeatherAPIError):
            fetch_forecast_weather("Tokyo", 35.6762, 139.6503, 1)
