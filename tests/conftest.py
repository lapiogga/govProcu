"""pytest 공통 설정."""
import os
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("G2B_KEY_BID", "test-key")
