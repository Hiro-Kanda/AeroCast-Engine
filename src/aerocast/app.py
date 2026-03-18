"""
AeroCast FastAPI アプリ（優先度1: PythonコアのAPI化）

起動: プロジェクトルートで
  python run_api.py
 または
  PYTHONPATH=src uvicorn aerocast.app:app --reload
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .schemas import ChatRequest, ChatResponse, WeatherQueryRequest, WeatherQueryResponse
from .agent_loop import run_structured
from .weather_api import fetch_weather
from .rules import decide_umbrella, decide_wind, decide_comfort
from .error import UserFacingError, CityNotFoundError, AmbiguousCityError
from .models import WeatherResult
from dataclasses import asdict


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # 必要ならクリーンアップ（例: セッション期限切れの削除）


app = FastAPI(
    title="AeroCast API",
    description="天気チャット・天気クエリAPI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api-info", response_class=HTMLResponse)
def api_info():
    """API 情報ページ（Docs へのリンク）"""
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>AeroCast API</title></head>
    <body style="font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem;">
        <h1>AeroCast API</h1>
        <p><a href="/">チャット画面へ</a></p>
        <ul>
            <li><a href="/docs">Swagger UI（API 仕様・試行）</a></li>
            <li><a href="/redoc">ReDoc（API 仕様）</a></li>
            <li><a href="/health">ヘルスチェック</a></li>
        </ul>
    </body>
    </html>
    """


@app.get("/health")
def health():
    """ヘルスチェック"""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """
    チャットメッセージを処理。
    セッションIDはフロントで保持し、バックは簡易辞書で管理（優先度4）。
    """
    try:
        result = run_structured(req.message, session_id=req.session_id)
        return ChatResponse(
            reply=result["reply"],
            location=result.get("location"),
            forecast=result.get("forecast"),
            judgement=result.get("judgement"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/weather/query", response_model=WeatherQueryResponse)
def weather_query(req: WeatherQueryRequest) -> WeatherQueryResponse:
    """
    都市・日数で天気を直接取得（エージェントを経由しない）。
    """
    try:
        weather: WeatherResult = fetch_weather(req.city, req.days)
        umbrella = decide_umbrella(weather)
        wind = decide_wind(weather)
        comfort = decide_comfort(weather)
        return WeatherQueryResponse(
            city=weather.city,
            days=req.days,
            forecast=asdict(weather),
            judgement={
                "umbrella": asdict(umbrella),
                "wind": asdict(wind),
                "comfort": asdict(comfort),
            },
        )
    except AmbiguousCityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UserFacingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 静的ファイル（チャット画面・CSS・画像）は API ルートの後にマウント
_static_dir = Path(__file__).resolve().parent / "static"
app.mount("/images", StaticFiles(directory=str(_static_dir / "images")), name="images")
app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
