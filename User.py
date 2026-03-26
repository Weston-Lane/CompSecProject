import time
from dataclasses import dataclass, field
from dataclasses import asdict
from typing import Optional

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    created_at: float = field(default_factory=time.time)
    role: str = "user"
    failed_attempts: int = 0
    locked_until: Optional[float] = None

    def AsDict(self):
        return asdict(self)