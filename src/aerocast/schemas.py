"""
API リクエスト/レスポンス用 Pydantic スキーマ
"""
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============== POST /chat ==============

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="フロントで保持するセッションID")
    message: str = Field(..., description="ユーザー発話")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="LLM整形文（表示用）")
    location: Optional[str] = Field(None, description="対象地域")
    forecast: Optional[dict[str, Any]] = Field(None, description="API取得値（WeatherResult）")
    judgement: Optional[dict[str, Any]] = Field(
        None,
        description="内部判定結果（umbrella, wind, comfort）",
    )


# ============== POST /weather/query ==============

class WeatherQueryRequest(BaseModel):
    city: str = Field(..., description="都市名")
    days: int = Field(0, ge=0, le=5, description="0=今日、1=明日〜5日後")


class WeatherQueryResponse(BaseModel):
    city: str = Field(..., description="都市名")
    days: int = Field(..., description="指定日数")
    forecast: dict[str, Any] = Field(..., description="API取得値（WeatherResult）")
    judgement: Optional[dict[str, Any]] = Field(
        None,
        description="内部判定（umbrella, wind, comfort）",
    )
