"""
AeroCast API サーバー起動スクリプト

使い方:
  python run_api.py

環境変数:
  OPENWEATHER_API_KEY ... 天気API（必須）
  OPENAI_API_KEY      ... LLM（/chat で使用）
"""
import os
import sys
from pathlib import Path

# プロジェクトルートと src をパスに追加（reload 時の子プロセス用に環境変数も設定）
src = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src))
os.environ.setdefault("PYTHONPATH", str(src))

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)

    import uvicorn

    port = 8000
    print(f"AeroCast API を起動しています...")
    print(f"  ブラウザで開く: http://localhost:{port}/")
    print(f"  API 仕様:       http://localhost:{port}/docs")
    print()

    uvicorn.run(
        "aerocast.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
