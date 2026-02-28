import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from config import SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    user_id: int
    video_id: Optional[str] = None
    video_title: Optional[str] = None
    transcript: Optional[str] = None
    language: str = "english"
    conversation_history: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_active = time.time()

    def is_expired(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES) -> bool:
        return (time.time() - self.last_active) > (timeout_minutes * 60)

    def has_video(self) -> bool:
        return self.video_id is not None and self.transcript is not None

    def set_video(self, video_id: str, transcript: str, title: str = "Unknown") -> None:
        self.video_id = video_id
        self.transcript = transcript
        self.video_title = title
        self.conversation_history = []
        self.touch()

    def add_qa(self, question: str, answer: str) -> None:
        self.conversation_history.append({"q": question, "a": answer})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        self.touch()

    def set_language(self, language: str) -> None:
        self.language = language.lower()
        self.touch()

    def clear(self) -> None:
        self.video_id = None
        self.video_title = None
        self.transcript = None
        self.language = "english"
        self.conversation_history = []
        self.touch()

class SessionManager:
    def __init__(self):
        self._sessions: dict[int, UserSession] = {}

    def get_session(self, user_id: int) -> UserSession:
        self._cleanup_expired()

        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
            logger.debug(f"New session created for user {user_id}")

        session = self._sessions[user_id]
        session.touch()
        return session

    def clear_session(self, user_id: int) -> None:
        if user_id in self._sessions:
            self._sessions[user_id].clear()

    def delete_session(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)

    def _cleanup_expired(self) -> None:
        expired = [
            uid for uid, session in self._sessions.items()
            if session.is_expired()
        ]
        for uid in expired:
            del self._sessions[uid]
            logger.debug(f"Expired session removed for user {uid}")

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)

session_manager = SessionManager()
