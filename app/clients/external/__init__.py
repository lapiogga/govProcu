"""외부 발주기관 OpenAPI 어댑터 — adapter dispatch 패턴.

각 어댑터는 BaseAgencyAdapter를 상속하고 search_bids() 표준 인터페이스를 구현한다.
multi_agency.py가 registry를 통해 dispatch.

키 발급 후 즉시 활성화: 각 어댑터의 SERVICE_KEY_ENV 환경변수가 설정되면 status='active'.
"""
from app.clients.external.base import BaseAgencyAdapter, AdapterStatus
from app.clients.external.lh import LHAdapter
from app.clients.external.ex import ExAdapter
from app.clients.external.kwater import KWaterAdapter
from app.clients.external.korail import KorailAdapter

__all__ = [
    "BaseAgencyAdapter",
    "AdapterStatus",
    "LHAdapter",
    "ExAdapter",
    "KWaterAdapter",
    "KorailAdapter",
    "ADAPTER_REGISTRY",
]

ADAPTER_REGISTRY: dict[str, type[BaseAgencyAdapter]] = {
    "lh": LHAdapter,
    "ex": ExAdapter,
    "kwater": KWaterAdapter,
    "korail": KorailAdapter,
}
