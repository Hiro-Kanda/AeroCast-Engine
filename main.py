import sys
from pathlib import Path

# srcディレクトリをPythonパスに追加
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv(override=True)

from aerocast import run_agent


def main():
    print("エージェント起動")
    while True:
        user_input = input("> ")
        if user_input.lower() in {"exit", "quit"}:
            break
        print(run_agent(user_input))

if __name__ == "__main__":
    main()