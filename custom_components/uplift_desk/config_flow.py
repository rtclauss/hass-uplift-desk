"""Config flow for the Uplift Desk integration."""

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .helpers import desk_title, is_valid_bluetooth_address, normalize_bluetooth_address

class UpliftDeskConfigFlow(ConfigFlow, domain=DOMAIN):
    """Uplift Desk config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak) -> ConfigFlowResult:
        """Handle a discovered Bluetooth device."""
        address = normalize_bluetooth_address(discovery_info.address)

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self._discovery_info is not None
        discovery_info = self._discovery_info
        address = normalize_bluetooth_address(discovery_info.address)
        title = desk_title(discovery_info.name, address)
        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={CONF_ADDRESS: address, CONF_NAME: title},
            )

        self._set_confirm_only()
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders=placeholders
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup when Bluetooth discovery is unavailable."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = normalize_bluetooth_address(user_input[CONF_ADDRESS])
            if not is_valid_bluetooth_address(address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                title = desk_title(user_input.get(CONF_NAME), address)
                return self.async_create_entry(
                    title=title,
                    data={CONF_ADDRESS: address, CONF_NAME: title},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
