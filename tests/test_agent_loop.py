from unittest.mock import patch

from aerocast.agent_loop import run_structured
from aerocast.intent_parser import WeatherIntent


@patch("aerocast.agent_loop.fetch_weather")
@patch("aerocast.agent_loop.parse_weather_intent")
def test_run_structured_returns_validation_message_for_invalid_days(
    mock_parse_weather_intent,
    mock_fetch_weather,
):
    mock_parse_weather_intent.return_value = WeatherIntent(city="譚ｱ莠ｬ", days=6)

    result = run_structured("ignored", session_id="test-invalid-days")

    assert "0" in result["reply"]
    assert "5" in result["reply"]
    mock_fetch_weather.assert_not_called()
