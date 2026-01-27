# AeroCast Engine

天気情報を取得し、データ化、予測の回答を行うAIエージェントシステムです。

## 概要

AeroCast Engineは、自然言語で天気に関する質問を受け取り、以下の機能を提供します：

- 天気情報の取得（現在・予報）
- 傘の必要性の判断
- 風速による注意喚起
- 体感温度による快適度の分類
- 雪確率の推定

## 特徴

- **ルールベース + LLM**: 判断はルールベース、説明はLLMを使用
- **信頼性重視**: LLM出力をバリデーションし、推測・推奨表現を排除
- **フォールバック機能**: LLM API障害時も基本機能を提供

## セットアップ

### 必要な環境

- Python 3.11以上
- OpenAI API Key
- OpenWeatherMap API Key

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd "AeroCast Engin"

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 環境変数

`.env`ファイルに以下を設定してください：

```
OPENWEATHER_API_KEY=your_openweather_api_key
OPENAI_API_KEY=your_openai_api_key
```

## 使用方法

### 基本的な使用

```bash
python main.py
```

対話形式で天気に関する質問ができます：

```
> 今日の東京の天気教えて
> 明日の札幌の天気は？
> 明後日の青森、雪降る？
```

### プログラムからの使用

```python
from aerocast import run_agent

result = run_agent("今日の東京の天気教えて")
print(result)
```

## アーキテクチャ

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Intent Parser│  ← 意図解析（都市名、日数）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Weather API │  ← 天気情報取得
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Rules    │  ← 判断（傘、風、快適度）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Formatter  │  ← LLMによる説明生成
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Output    │
└─────────────┘
```

詳細は [docs/MODELS.md](docs/MODELS.md) を参照してください。

## テスト

```bash
# 全テストの実行
pytest

# 特定のテストの実行
pytest tests/test_rules.py
pytest tests/test_benchmark.py

# カバレッジの確認
pytest --cov=src/aerocast
```

## プロジェクト構造

```
AeroCast Engin/
├── src/aerocast/          # メインパッケージ
│   ├── agent.py          # エージェントのメインロジック
│   ├── intent_parser.py  # 意図解析
│   ├── weather_api.py    # 天気API連携
│   ├── rules.py          # 判断ルール
│   ├── formatter.py      # LLMフォーマッター
│   ├── snow_estimator.py # 雪確率推定モデル
│   ├── validators.py     # バリデーション
│   └── models.py         # データモデル
├── tests/                # テスト
│   ├── data/             # テストデータ
│   │   └── benth_cases.jsonl
│   └── test_*.py
├── docs/                 # ドキュメンテーション
│   └── MODELS.md
└── main.py               # エントリーポイント
```

## モデルとアルゴリズム

詳細な仕様は [docs/MODELS.md](docs/MODELS.md) を参照してください。

### 主要なモデル

1. **雪確率推定モデル**: 降水確率と気温から雪確率を推定
2. **意図解析モデル**: 自然言語から都市名と日数を抽出
3. **判断ルール**: 傘、風速、快適度の判断

## 評価

ベンチマークデータを使用した評価が可能です：

```bash
pytest tests/test_benchmark.py -v
```

評価データは `tests/data/benth_cases.jsonl` にあります。

## ライセンス

[ライセンス情報を記載]

## 貢献

[貢献方法を記載]

## 参考文献

- OpenWeatherMap API: https://openweathermap.org/api
- OpenAI API: https://platform.openai.com/docs
