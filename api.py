from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import aiohttp
import json

from .const import API_URL


class AlyenergiaApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str, refresh_token: str | None = None) -> None:
        self.session = session
        self.username = username
        self.password = password
        self.access_token: str | None = None
        self.refresh_token = refresh_token

    async def async_login(self) -> None:
        data = await self._request("auth.login", {"email": self.username, "password": self.password}, authenticated=False)
        self._set_tokens(data)

    async def async_refresh(self) -> None:
        if not self.refresh_token:
            await self.async_login()
            return
        data = await self._request("auth.refresh", {"refreshToken": self.refresh_token}, authenticated=False)
        self._set_tokens(data)

    def _set_tokens(self, data: dict[str, Any]) -> None:
        self.access_token = data["accessToken"]
        self.refresh_token = data.get("refreshToken", self.refresh_token)

    async def _request(self, procedure: str, payload: dict[str, Any], authenticated: bool = True) -> Any:
        headers = {"content-type": "application/json"}
        if authenticated and self.access_token:
            headers["authorization"] = f"Bearer {self.access_token}"
        async with self.session.post(API_URL + procedure, json=payload, headers=headers) as response:
            response.raise_for_status()
            body = await response.json()
        return body["result"]["data"]

    async def _query(self, procedure: str, payload: dict[str, Any]) -> Any:
        headers = {"authorization": f"Bearer {self.access_token}"}
        url = f"{API_URL}{procedure}?input={quote(json.dumps(payload, separators=(',', ':')))}"
        async with self.session.get(url, headers=headers) as response:
            if response.status == 401:
                await self.async_refresh()
                headers["authorization"] = f"Bearer {self.access_token}"
                async with self.session.get(url, headers=headers) as retry:
                    retry.raise_for_status()
                    return (await retry.json())["result"]["data"]
            response.raise_for_status()
            return (await response.json())["result"]["data"]

    async def async_data(self) -> dict[str, Any]:
        user = await self._query("user.currentUser", {})
        account = user.get("user", user)
        objects = await self._query("user.getObjects", {"userId": account["id"]})
        if not objects:
            raise ValueError("No electricity object found")
        object_data = objects[0]
        object_id = object_data["id"]
        contract_id = object_data["synerallContractId"]
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 1:
            previous_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            previous_start = month_start.replace(month=month_start.month - 1)
        previous_end = month_start
        current = await self._query("objects.getConsumption", {"objectId": object_id, "from": month_start.isoformat(), "to": now.isoformat()})
        previous = await self._query("objects.getConsumption", {"objectId": object_id, "from": previous_start.isoformat(), "to": previous_end.isoformat()})
        is_spot_margin = object_data.get("contractType") == "spot"
        price = float(object_data.get("spotMarginal", 0)) if is_spot_margin else float(object_data.get("fixedPrice", 0))
        invoice_current = await self._query("objects.getInvoiceAccumulation", {"objectId": object_id, "from": month_start.isoformat(), "to": now.isoformat(), "isSpotMargin": is_spot_margin, "price": price, "groupBy": "month"})
        invoice_previous = await self._query("objects.getInvoiceAccumulation", {"objectId": object_id, "from": previous_start.isoformat(), "to": previous_end.isoformat(), "isSpotMargin": is_spot_margin, "price": price, "groupBy": "month"})
        invoices = await self._query("synerall.invoices", {"contractId": contract_id})
        latest_reading = max(
            current.get("groupedData", []),
            key=lambda item: item.get("localTime", {}).get("unix", 0),
            default={},
        )
        current_cost = _cost(invoice_current)
        previous_cost = _cost(invoice_previous)
        current_kwh = float(current.get("totalConsumption", 0))
        previous_kwh = float(previous.get("totalConsumption", 0))
        latest_invoice = max(invoices, key=lambda item: item.get("IssuedDate", "")) if invoices else {}
        return {
            "latest_consumption": latest_reading.get("kwh"),
            "latest_consumption_timestamp": latest_reading.get("StartHourUTC"),
            "current_consumption": current_kwh,
            "current_cost": current_cost,
            "current_mean_price": current_cost / current_kwh if current_kwh else None,
            "previous_consumption": previous_kwh,
            "previous_cost": previous_cost,
            "previous_mean_price": previous_cost / previous_kwh if previous_kwh else None,
            "latest_invoice_balance": latest_invoice.get("Balance"),
            "latest_invoice_date": latest_invoice.get("IssuedDate"),
        }


def _cost(value: Any) -> float:
    if not value:
        return 0.0
    item = value[-1] if isinstance(value, list) else value
    return float(item.get("invoiceAccumulationWithTransferInEur", item.get("invoiceAccumulationInEur", 0)))
