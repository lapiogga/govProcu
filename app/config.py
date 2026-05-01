"""환경변수 로딩 (Pydantic Settings)."""
from __future__ import annotations
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 설정."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # G2B 키
    g2b_key_bid: str = Field(default="", description="입찰공고정보서비스")
    g2b_key_prespec: str = Field(default="", description="사전규격정보서비스")
    g2b_key_award: str = Field(default="", description="낙찰정보서비스")
    g2b_key_vendor: str = Field(default="", description="입찰참가자격등록정보")
    g2b_key_user: str = Field(default="", description="사용자정보서비스")
    g2b_key_stats: str = Field(default="", description="공공조달통계정보서비스")

    # MCP 인증
    mcp_api_tokens: str = Field(default="", description="콤마 구분 토큰 목록")

    @property
    def allowed_tokens(self) -> set[str]:
        return {t.strip() for t in self.mcp_api_tokens.split(",") if t.strip()}

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_short: int = 300
    cache_ttl_long: int = 86400

    # 운영
    log_level: str = "INFO"
    server_host: str = "0.0.0.0"
    server_port: int = 8080

    # G2B 공통
    g2b_base_url: str = "http://apis.data.go.kr/1230000"


settings = Settings()
