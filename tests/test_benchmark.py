"""
ベンチマークケースを使用したシステム評価

tests/data/benth_cases.jsonl の各ケースに対してシステムを実行し、
意図解析の精度を評価します。
"""
import json
import pytest
from pathlib import Path
from aerocast import run_agent
from aerocast.intent_parser import parse_weather_intent


def load_benchmark_cases():
    """ベンチマークケースを読み込む"""
    benchmark_file = Path(__file__).parent / "data" / "benth_cases.jsonl"
    if not benchmark_file.exists():
        pytest.skip(f"ベンチマークファイルが見つかりません: {benchmark_file}")
    
    cases = []
    with open(benchmark_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


class TestBenchmarkCases:
    """ベンチマークケースのテスト"""

    @pytest.mark.parametrize("case", load_benchmark_cases())
    def test_intent_parsing(self, case):
        """意図解析の精度テスト"""
        intent = parse_weather_intent(case["input"])
        
        assert intent is not None, f"入力 '{case['input']}' の意図解析に失敗"
        assert intent.city == case["city"], (
            f"都市名の解析が不一致: 期待={case['city']}, 実際={intent.city}"
        )
        assert intent.days == case["days"], (
            f"日数の解析が不一致: 期待={case['days']}, 実際={intent.days}"
        )

    @pytest.mark.parametrize("case", load_benchmark_cases())
    def test_agent_execution(self, case):
        """エージェントの実行テスト（API呼び出しはモック推奨）"""
        # 注意: このテストは実際のAPIを呼び出すため、
        # 環境変数が設定されている場合のみ実行される
        import os
        if not os.getenv("OPENWEATHER_API_KEY"):
            pytest.skip("OPENWEATHER_API_KEYが設定されていません")
        
        result = run_agent(case["input"])
        
        # 結果が空でないことを確認
        assert result is not None
        assert len(result) > 0
        
        # エラーメッセージでないことを確認
        assert "問題が発生" not in result
        assert "対応していません" not in result or case["city"] in result


def test_benchmark_coverage():
    """ベンチマークケースのカバレッジ確認"""
    cases = load_benchmark_cases()
    assert len(cases) > 0, "ベンチマークケースが存在しません"
    
    # 各ケースに必要なフィールドがあることを確認
    for i, case in enumerate(cases):
        assert "input" in case, f"ケース {i+1} に 'input' フィールドがありません"
        assert "city" in case, f"ケース {i+1} に 'city' フィールドがありません"
        assert "days" in case, f"ケース {i+1} に 'days' フィールドがありません"
