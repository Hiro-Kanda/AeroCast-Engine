# AeroCast Engine

天気情報を取得し、データ化・判定・表示用テキスト生成まで行うエージェントシステムです。自然言語で質問でき、REST API とチャット UI を備えています。

## 概要

AeroCast Engine は、自然言語で天気に関する質問を受け取り、以下の機能を提供します。

- 天気情報の取得（現在・予報、0〜5日後）
- 傘の必要性の判断
- 風速による注意喚起
- 体感温度による快適度の分類
- 雪確率の推定
- **REST API**（FastAPI）: チャット・天気クエリ・ヘルスチェック
- **チャット UI**: 天気に応じた背景・エフェクト（晴れ・曇り・雨・雪・雷・風・嵐）

## 特徴

- **ルールベース + オプションで LLM**: 判定はルールベース。表示文はルールベースの Markdown 整形をメインとし、LLM はフォールバック用。
- **信頼性重視**: バリデーションとフォールバックにより、API 障害時も基本機能を提供。
- **構造化レスポンス**: `reply`（表示用文）・`forecast`（API 取得値）・`judgement`（傘・風・快適度）を分けて返却。

## セットアップ

### 必要な環境

- Python 3.11 以上
- OpenWeatherMap API Key（必須）
- OpenAI API Key（LLM フォールバックを使う場合のみ）

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd AeroCast-Engine

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定（プロジェクトルートに .env を作成）
# .env の内容例:
# OPENWEATHER_API_KEY=your_openweather_api_key
# OPENAI_API_KEY=your_openai_api_key  # オプション
```

### 環境変数

`.env` ファイルをプロジェクトルートに作成し、以下を設定してください。

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `OPENWEATHER_API_KEY` | はい | OpenWeatherMap の API キー |
| `OPENAI_API_KEY` | いいえ | LLM フォールバック用（未設定時はルールベースのみ） |

## 使用方法

### CLI（対話形式）

```bash
python main.py
```

対話形式で天気に関する質問ができます。

```
> 今日の東京の天気教えて
> 明日の札幌の天気は？
> clear   # セッションクリア
> exit    # 終了
```

### プログラムからの使用

```python
from aerocast import run_agent, run_structured

# 文字列で回答のみ取得（CLI と同じ）
result = run_agent("今日の東京の天気教えて", session_id="my-session")
print(result)

# 構造化レスポンス（API 向け）
data = run_structured("明日の大阪の天気は？", session_id="my-session")
# data["reply"], data["location"], data["forecast"], data["judgement"]
```

### API サーバー（FastAPI）

```bash
pip install -r requirements.txt
python run_api.py
```

- デフォルト: `http://0.0.0.0:8000`
- **GET /** … チャット UI
- **GET /api-info** … API 情報・Docs へのリンク
- **GET /health** … ヘルスチェック
- **POST /chat** … チャット（セッション付き）
- **POST /weather/query** … 都市・日数で天気を直接取得

レスポンスでは **reply**（表示用整形文）・**forecast**（API 取得値）・**judgement**（内部判定）を分けて返します。詳細は [docs/API.md](docs/API.md) を参照してください。

### チャット UI

`python run_api.py` 起動後、ブラウザで `http://localhost:8000/` にアクセスするとチャット画面が開きます。

- 天気に応じて背景色とエフェクトが変化（晴れ・曇り・雨・雪・雷・嵐・強風）
- 送信は送信ボタンのみ（Enter は改行）
- セッションはブラウザ側で保持され、会話の文脈で「明日の天気」のように続けて質問可能

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
│ Weather API │  ← 天気情報取得（OpenWeatherMap）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Rules    │  ← 判断（傘・風・快適度）
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Weather Summary  │  ← 要約（日付・気温・降水など）
│ Advice Engine   │  ← 生活アドバイス生成
│ Formatter       │  ← Markdown 整形（ルールベース / オプションで LLM）
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   Output    │  ← reply / forecast / judgement
└─────────────┘
```

パイプラインの詳細は [docs/MODELS.md](docs/MODELS.md) を参照してください。コードのレビュー概要は [docs/REVIEW.md](docs/REVIEW.md) を参照してください。

## テスト

```bash
# 全テストの実行
pytest tests/ -v

# 特定のテスト
pytest tests/test_rules.py -v
pytest tests/test_benchmark.py -v

# カバレッジ
pytest tests/ --cov=src/aerocast
```

## プロジェクト構造

```
AeroCast-Engine/
├── main.py                 # CLI エントリ
├── run_api.py              # API サーバー起動
├── requirements.txt
├── src/aerocast/           # メインパッケージ
│   ├── app.py              # FastAPI アプリ・ルート定義
│   ├── schemas.py          # API リクエスト/レスポンス（Pydantic）
│   ├── agent_loop.py       # エージェントループ・run_structured
│   ├── agent.py            # run_agent（CLI 向けラッパー）
│   ├── state.py            # AgentState
│   ├── actions.py          # Action 列挙
│   ├── intent_parser.py    # 意図解析（都市名・日数）
│   ├── weather_api.py     # 天気 API 連携
│   ├── weather_summary.py # API 応答の要約（WeatherSummary）
│   ├── advice_engine.py    # 生活アドバイス（AdviceResult）
│   ├── formatter.py       # Markdown 整形（format_to_markdown / format_weather）
│   ├── fallback_formatter.py
│   ├── rules.py           # 傘・風・快適度の判定
│   ├── models.py          # データモデル
│   ├── snow_estimator.py  # 雪確率推定
│   ├── validators.py
│   ├── session.py         # セッション管理（インメモリ）
│   ├── preprocessor.py
│   ├── error.py
│   ├── retry.py
│   ├── logger.py
│   └── static/            # チャット UI
│       ├── index.html
│       ├── css/style.css
│       └── images/
├── tests/
│   ├── data/
│   └── test_*.py
└── docs/
    ├── API.md
    ├── MODELS.md
    └── REVIEW.md
```

## モデルとアルゴリズム

- **雪確率推定**: 降水確率と気温から雪確率を推定
- **意図解析**: 自然言語から都市名と日数（0〜5）を抽出
- **判断ルール**: 傘・風速・快適度の判定

詳細は [docs/MODELS.md](docs/MODELS.md) を参照してください。

## 評価

ベンチマークデータによる評価:

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
