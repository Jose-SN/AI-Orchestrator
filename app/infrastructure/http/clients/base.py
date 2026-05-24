"""Base async HTTP client."""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.exceptions import DownstreamServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseHTTPClient:
    def __init__(self, base_url: str, service_name: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = httpx.Timeout(timeout_seconds)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        url = path if path.startswith("/") else f"/{path}"
        try:
            response = await client.request(method=method, url=url, headers=headers, params=params, json=json)
            response.raise_for_status()
            if response.content:
                data = response.json()
                return data if isinstance(data, dict) else {"data": data}
            return {}
        except httpx.HTTPStatusError as exc:
            raise DownstreamServiceError(
                f"{self.service_name} returned HTTP {exc.response.status_code}",
                service=self.service_name,
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise DownstreamServiceError(
                f"Failed to reach {self.service_name}: {exc}",
                service=self.service_name,
            ) from exc

    async def get(self, path: str, *, token: str | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("GET", path, token=token, params=params)

    async def post(self, path: str, *, token: str | None = None, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("POST", path, token=token, json=json)
