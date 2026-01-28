"""
会話セッション管理
文脈を保持して、省略された入力を補完する
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class ConversationContext:
    """会話の文脈情報"""
    last_city: Optional[str] = None
    last_days: Optional[int] = None
    last_intent: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    # セッションの有効期限（デフォルト30分）
    session_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    
    def is_expired(self) -> bool:
        """セッションが期限切れかどうか"""
        if self.last_updated is None:
            return False
        return datetime.now() - self.last_updated > self.session_timeout
    
    def update(self, city: Optional[str] = None, days: Optional[int] = None, intent: Optional[str] = None):
        """文脈を更新"""
        if city is not None:
            self.last_city = city
        if days is not None:
            self.last_days = days
        if intent is not None:
            self.last_intent = intent
        self.last_updated = datetime.now()
    
    def clear(self):
        """文脈をクリア"""
        self.last_city = None
        self.last_days = None
        self.last_intent = None
        self.last_updated = None


class SessionManager:
    """セッションマネージャー（シンプルなインメモリ実装）"""
    
    def __init__(self):
        self._sessions: dict[str, ConversationContext] = {}
    
    def get_context(self, session_id: str) -> ConversationContext:
        """セッションの文脈を取得（なければ新規作成）"""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationContext()
        else:
            context = self._sessions[session_id]
            if context.is_expired():
                context.clear()
        return self._sessions[session_id]
    
    def clear_session(self, session_id: str):
        """セッションをクリア"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_expired(self):
        """期限切れのセッションをクリーンアップ"""
        expired_keys = [
            key for key, context in self._sessions.items()
            if context.is_expired()
        ]
        for key in expired_keys:
            del self._sessions[key]


# グローバルセッションマネージャー（シンプルな実装）
_global_session_manager = SessionManager()


def get_session_context(session_id: str = "default") -> ConversationContext:
    """グローバルセッションマネージャーから文脈を取得"""
    return _global_session_manager.get_context(session_id)


def clear_session(session_id: str = "default"):
    """セッションをクリア"""
    _global_session_manager.clear_session(session_id)
