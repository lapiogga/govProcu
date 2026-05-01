"""G2B 에러 코드를 LLM 친화적 카테고리로 정규화."""
from __future__ import annotations
from enum import Enum


class ErrorCategory(str, Enum):
    INVALID_PARAM = "invalid_param"
    RATE_LIMIT = "rate_limit"
    NOT_REGISTERED = "not_registered"
    UPSTREAM_5XX = "upstream_5xx"
    NETWORK = "network"
    UNKNOWN = "unknown"


G2B_ERROR_MAP = {
    "00": None,  # NORMAL
    "01": ErrorCategory.INVALID_PARAM,  # APPLICATION_ERROR
    "02": ErrorCategory.NETWORK,        # DB_ERROR
    "03": ErrorCategory.UNKNOWN,        # NODATA_ERROR
    "04": ErrorCategory.NETWORK,        # HTTP_ERROR
    "05": ErrorCategory.NETWORK,        # SERVICETIMEOUT_ERROR
    "10": ErrorCategory.INVALID_PARAM,  # INVALID_REQUEST_PARAMETER
    "12": ErrorCategory.NOT_REGISTERED, # NO_OPENAPI_SERVICE
    "20": ErrorCategory.NOT_REGISTERED, # SERVICE_ACCESS_DENIED
    "22": ErrorCategory.RATE_LIMIT,     # LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS
    "30": ErrorCategory.NOT_REGISTERED, # SERVICE_KEY_IS_NOT_REGISTERED
    "31": ErrorCategory.NOT_REGISTERED, # DEADLINE_HAS_EXPIRED
    "32": ErrorCategory.NOT_REGISTERED, # UNREGISTERED_IP
    "33": ErrorCategory.NOT_REGISTERED, # UNSIGNED_CALL
    "99": ErrorCategory.UNKNOWN,        # UNKNOWN_ERROR
}


class G2BError(Exception):
    def __init__(self, code: str, message: str, category: ErrorCategory):
        self.code = code
        self.message = message
        self.category = category
        super().__init__(f"[{category.value}] {code}: {message}")


def map_g2b_response(header: dict) -> None:
    """G2B 응답 header를 검증하고 비정상 시 G2BError 발생."""
    code = str(header.get("resultCode", "")).strip()
    msg = header.get("resultMsg", "")
    if code == "00":
        return
    cat = G2B_ERROR_MAP.get(code, ErrorCategory.UNKNOWN)
    raise G2BError(code, msg, cat)
