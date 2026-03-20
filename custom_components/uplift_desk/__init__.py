"""The Uplift Desk integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import BLEAK_TIMEOUT_SECONDS, DOMAIN
from .coordinator import (
    UpliftDeskBluetoothCoordinator,
    Uplift_Desk_DeskConfigEntry,
)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: Uplift_Desk_DeskConfigEntry) -> bool:
    """Set up Uplift Desk from a config entry."""

    address = entry.data[CONF_ADDRESS]

    ble_device = async_ble_device_from_address(hass, address)
    if not ble_device:
        _LOGGER.warning("Uplift Desk %s was not found in the Bluetooth device cache", address)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"address": address},
        )

    coordinator = UpliftDeskBluetoothCoordinator(hass, entry, ble_device)
    entry.runtime_data = coordinator

    try:
        async with asyncio.timeout(BLEAK_TIMEOUT_SECONDS):
            await coordinator.async_connect()
        try:
            async with asyncio.timeout(BLEAK_TIMEOUT_SECONDS):
                await coordinator.async_read_desk_height()
        except TimeoutError:
            _LOGGER.warning(
                "Initial height read timed out for %s; continuing setup",
                address,
            )
    except Exception as err:
        _LOGGER.exception(
            "Failed to initialize Uplift Desk for %s at %s",
            entry.title,
            address,
        )
        await coordinator.async_disconnect()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"address": address},
        ) from err

    _LOGGER.debug(
        "Initialized Uplift Desk for %s at %s", entry.title, entry.data[CONF_ADDRESS]
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: Uplift_Desk_DeskConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: UpliftDeskBluetoothCoordinator = entry.runtime_data

    await coordinator.async_disconnect()

    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
