from .agent_loop import run as run_agent_loop


def run_agent(user_input: str, session_id: str = "default") -> str:
    """
    エージェントを実行（後方互換性のため）
    
    Args:
        user_input: ユーザー入力
        session_id: セッションID（会話の文脈を保持するため）
    
    Returns:
        天気情報の説明文
    """
    # 新しいエージェントループを使用
    return run_agent_loop(user_input, session_id=session_id)
    