from __future__ import annotations

import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlyenergiaApi
from .const import CONF_PASSWORD, CONF_REFRESH_TOKEN, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlyenergiaCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api = AlyenergiaApi(
            async_get_clientsession(hass),
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data.get(CONF_REFRESH_TOKEN),
        )
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=datetime.timedelta(days=1))

    async def _async_update_data(self) -> dict:
        try:
            if not self.api.access_token:
                await self.api.async_refresh()
            result = await self.api.async_data()
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch Vihrea Alyenergia data: {err}") from err
        if self.api.refresh_token != self.entry.data.get(CONF_REFRESH_TOKEN):
            self.hass.config_entries.async_update_entry(self.entry, data={**self.entry.data, CONF_REFRESH_TOKEN: self.api.refresh_token})
        return result
