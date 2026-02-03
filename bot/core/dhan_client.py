from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from bot.utils.logger import setup_logger


@dataclass(frozen=True)
class DhanCredentials:
    client_id: str
    access_token: str
    base_url: str


class DhanClient:
    def __init__(self, credentials: DhanCredentials) -> None:
        self._credentials = credentials
        self._logger = setup_logger(self.__class__.__name__)

    def _headers(self) -> dict[str, str]:
        return {
            "ClientID": self._credentials.client_id,
            "access-token": self._credentials.access_token,
            "Content-Type": "application/json",
        }

    def get_instruments(self) -> list[dict[str, Any]]:
        url = f"{self._credentials.base_url}/instruments"
        self._logger.info("Fetching instrument master")
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Instrument master response is invalid")
        return payload

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._credentials.base_url}/orders"
        self._logger.info("Placing order", extra={"payload": payload})
        response = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_positions(self) -> list[dict[str, Any]]:
        url = f"{self._credentials.base_url}/positions"
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Positions response is invalid")
        return payload
