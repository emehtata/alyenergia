from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlyenergiaApi
from .const import CONF_REFRESH_TOKEN, DOMAIN


class AlyenergiaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            api = AlyenergiaApi(async_get_clientsession(self.hass), username, password)
            try:
                await api.async_login()
                user = await api._query("user.currentUser", {})
            except (aiohttp.ClientError, KeyError, ValueError):
                errors["base"] = "invalid_auth"
            else:
                account = user.get("user", user)
                account_id = account.get("id")
                if account_id is None:
                    errors["base"] = "invalid_auth"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): vol.All(str, vol.Length(min=1))}),
                        errors=errors,
                    )
                await self.async_set_unique_id(str(account_id))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Vihrea Alyenergia",
                    data={CONF_USERNAME: username, CONF_PASSWORD: password, CONF_REFRESH_TOKEN: api.refresh_token},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): vol.All(str, vol.Length(min=1))}),
            errors=errors,
        )
