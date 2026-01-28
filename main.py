import sys
from pathlib import Path
import uuid

# srcディレクトリをPythonパスに追加
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv(override=True)

from aerocast import run_agent
from aerocast.session import clear_session


def main():
    print("エージェント起動")
    print("（会話の文脈を保持します。'clear'でセッションをクリア、'exit'または'quit'で終了）")
    
    # セッションIDを生成（実際のアプリではユーザーIDなどから生成）
    session_id = str(uuid.uuid4())
    
    while True:
        user_input = input("> ")
        if user_input.lower() in {"exit", "quit"}:
            print("終了します。")
            break
        if user_input.lower() == "clear":
            clear_session(session_id)
            print("セッションをクリアしました。")
            continue
        
        result = run_agent(user_input, session_id=session_id)
        print(result)
        print()  # 空行を追加

if __name__ == "__main__":
    main()