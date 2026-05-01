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
    g2b_key_contract: str = Field(default="", description="계약과정통합공개정보")
    g2b_key_user: str = Field(default="", description="사용자정보서비스")
    g2b_key_stats: str = Field(default="", description="공공조달통계정보서비스")
    g2b_key_eval: str = Field(default="", description="평가정보/응찰업체 상세 (조달데이터허브 신규 신청)")

    # 국세청 사업자등록 진위확인 및 상태조회
    nts_api_key: str = Field(default="", description="국세청 사업자등록 상태조회 인증키 (data.go.kr 발급, Decoding 권장)")

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

    # G2B 공통 (운영 검증된 경로: https + /ad 프리픽스)
    g2b_base_url: str = "https://apis.data.go.kr/1230000/ad"

    # NTS 사업자등록 진위확인/상태조회 (data.go.kr odcloud)
    nts_base_url: str = "https://api.odcloud.kr/api/nts-businessman/v1"


settings = Settings()
