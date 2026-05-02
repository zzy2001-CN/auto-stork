from __future__ import annotations

import time
from typing import Any

import requests
from requests import RequestException


class HttpError(RuntimeError):
    pass


def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 2,
    backoff: float = 1.0,
) -> dict[str, Any]:
    response = request("GET", url, params=params, headers=headers, timeout=timeout, retries=retries, backoff=backoff)
    try:
        return response.json()
    except ValueError as exc:
        raise HttpError(f"Invalid JSON from {url}") from exc


def get_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 2,
    backoff: float = 1.0,
) -> str:
    return request("GET", url, params=params, headers=headers, timeout=timeout, retries=retries, backoff=backoff).text


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
    timeout: int,
    retries: int,
    backoff: float,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, params=params, headers=headers, timeout=timeout)
        except RequestException as exc:
            last_error = exc
        else:
            if response.status_code < 400:
                return response
            if response.status_code not in {429, 500, 502, 503, 504} or attempt >= retries:
                raise HttpError(f"{method} {url} failed with HTTP {response.status_code}: {response.text[:300]}")
            last_error = HttpError(f"{method} {url} failed with HTTP {response.status_code}")

        if attempt < retries:
            time.sleep(backoff * (2**attempt))

    raise HttpError(f"{method} {url} failed: {last_error}") from last_error

