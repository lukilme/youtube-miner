import time
import requests
from typing import Dict, Any
from src.core.models.api_data_classes import RateLimitConfig, YouTubeAuthError, YouTubeAPIError, CommentsDisabledError
import logging
from src.core.setting.logger import setup_logger
logger: logging.Logger = setup_logger("youtube_requester")

class YouTubeAPIRequester:
    def __init__(
        self,
        api_key: str,
        timeout: int = 20,
        retries: int = 3,
        backoff_base: float = 2.0,
        rate_config: RateLimitConfig | None = None,
    ) -> None:
        self._api_key = api_key
        self._session = requests.Session()
        self.timeout = timeout
        self.retries = retries
        self.backoff_base = backoff_base
        self.rate_config = rate_config or RateLimitConfig()

        # Controle interno de throttling
        self._last_request_ts = 0.0
        self._burst_tokens = self.rate_config.burst

    @property
    def api_key(self) -> str:
        return self._api_key

    def _throttle(self) -> None:
        if self.rate_config.requests_per_second <= 0:
            return
        min_interval = 1.0 / self.rate_config.requests_per_second
        now = time.monotonic()
        elapsed = now - self._last_request_ts

        if self._burst_tokens > 0:
            self._burst_tokens -= 1
        else:
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

        self._last_request_ts = time.monotonic()
        if elapsed >= min_interval and self._burst_tokens < self.rate_config.burst:
            self._burst_tokens = min(self._burst_tokens + 1, self.rate_config.burst)

    def get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa requisição GET com retry e tratamento de erros."""
        params = {**params, "key": self._api_key}  # garante que a chave esteja presente
        last_exc: Exception = RuntimeError("No attempts made.")

        for attempt in range(1, self.retries + 1):
            try:
                self._throttle()
                resp = self._session.get(url, params=params, timeout=self.timeout)
                self._raise_for_status(resp)
                return resp.json()
            except (requests.RequestException, YouTubeAPIError) as exc:
                last_exc = exc
                if attempt < self.retries:
                    wait = self.backoff_base ** (attempt - 1)
                    logger.warning(
                        "Tentativa %d/%d falhou (%s). Aguardando %.1fs…",
                        attempt,
                        self.retries,
                        exc,
                        wait,
                    )
                    time.sleep(wait)

        raise YouTubeAPIError(f"Falha após {self.retries} tentativas: {last_exc}") from last_exc

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.status_code == 200:
            return
        body = resp.text[:500]
        if resp.status_code == 401:
            raise YouTubeAuthError(f"Não autorizado (401): {body}")
        if resp.status_code == 403:
            try:
                error_data = resp.json()
                message = error_data.get("error", {}).get("message", "").lower()
                if "disabled comments" in message:
                    raise CommentsDisabledError(message)
            except ValueError:
                pass
            raise YouTubeAPIError(f"Proibido/Cota (403): {resp.text}")
        resp.raise_for_status()
        raise YouTubeAPIError(f"HTTP {resp.status_code}: {body}")