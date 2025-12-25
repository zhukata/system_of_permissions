from enum import Enum


class AccessAction(str, Enum):
    GRANT = "GRANT"
    REVOKE = "REVOKE"


class AccessRequestStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
