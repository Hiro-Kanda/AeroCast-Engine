# AeroCast API

優先度1で追加した FastAPI エンドポイントの仕様です。

## 起動

```bash
# プロジェクトルートで
pip install -r requirements.txt
python run_api.py
```

- デフォルト: `http://0.0.0.0:8000`
- ヘルス: `http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/docs`

## エンドポイント

### GET /health

ヘルスチェック。

**Response**

```json
{ "status": "ok" }
```

---

### POST /chat

チャットメッセージを処理。意図解析・天気取得・判定・LLM整形まで一括で実行します。  
セッションIDはフロントで保持し、バックエンドは簡易辞書でセッション管理（優先度4）。

**Request**

```json
{
  "session_id": "abc123",
  "message": "明日の東京の天気は？"
}
```

**Response（天気取得が成功した場合）**

```json
{
  "reply": "（LLMが生成した説明文）",
  "location": "東京",
  "forecast": {
    "city": "東京",
    "weather": "晴れ",
    "temp": 22.5,
    "feels_like": 21.0,
    "humidity": 60,
    "rain_probability": 10,
    "wind_speed": 2.5,
    "type": "forecast",
    ...
  },
  "judgement": {
    "umbrella": { "needed": false, "rain_code": "RAIN_PROB_LT_40" },
    "wind": { "alert": false, "wind_speed": 2.5, "reason_code": "WIND_LT_10" },
    "comfort": { "level": "WARM", "feels_like": 21.0, "reason_code": "FEELS_LIKE_TEMP" }
  }
}
```

- `reply`: LLM整形文（表示用）
- `location`: 対象地域
- `forecast`: API取得値（WeatherResult 相当）
- `judgement`: 内部判定結果（傘・風・快適度）

曖昧な質問やエラー時は `reply` のみが入り、`location` / `forecast` / `judgement` は `null` になります。

---

### POST /weather/query

都市名と日数で天気を直接取得（エージェント・チャットを経由しない）。

**Request**

```json
{
  "city": "東京",
  "days": 0
}
```

- `days`: 0=今日、1=明日、… 5=5日後（0〜5）

**Response**

```json
{
  "city": "東京",
  "days": 0,
  "forecast": { ... },
  "judgement": { "umbrella": {...}, "wind": {...}, "comfort": {...} }
}
```

- 都市が曖昧・未解決: 400
- 都市が見つからない: 404

## セッション（優先度4）

- **現状**: フロントで `session_id` を生成・保持し、`/chat` のたびに送る。バックエンドは `session.py` のインメモリ辞書で文脈を保持。
- **将来**: Redis や DB での永続化を検討。

## レスポンスの構造化（優先度3）

`formatter` の前後で以下を分けて返しています。

| 項目 | 内容 |
|------|------|
| 内部判定結果 | `judgement`（傘・風・快適度） |
| API取得値 | `forecast`（WeatherResult） |
| LLM整形文 | `reply` |

UI では `reply` をそのまま表示し、必要に応じて `forecast` / `judgement` でカードやバッジを組み立てられます。
