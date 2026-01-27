import pytest
from aerocast.validators import validate_llm_output, LLMOutputValidation

def test_valid_text():
    validate_llm_output("今日の東京の天気は晴れです。")

def test_forbidden_text():
    with pytest.raises(LLMOutputValidation):
        validate_llm_output("防寒対策をお勧めします")