"""The Uplift Desk integration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import traceback

from uplift_ble.desk_controller import DeskController
from uplift_ble.desk_validator import DeskValidator
from uplift_ble.desk_enums import DeskEventType
from uplift_ble.ble_protos import (
    BLEClientProtocol,
    BLEDeviceProtocol
)

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.core import HomeAssistant

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import DOMAIN, BLEAK_TIMEOUT_SECONDS
from .models import DiscoveredDesk

type Uplift_Desk_DeskConfigEntry = ConfigEntry[UpliftDeskBluetoothCoordinator]  # noqa: F821

_LOGGER: logging.Logger = logging.getLogger(__name__)

# Fallback target when desk never reports its height limit.
# Jiecang firmware clamps to the desk's programmed maximum, so sending a
# value larger than any real desk height is safe.
_MAX_HEIGHT_TENTHS_MM_FALLBACK = 0xFFFF  # 6553.5 mm ≈ 21 ft

def convert_mm_to_in(millimeters: int | float) -> float:
    """Convert millimeters to inches."""
    return millimeters / 25.4

def _generate_existing_client_factory(bleak_client: BleakClient) -> Callable[..., BLEClientProtocol]:
    def _existing_client_factory(
        device: BLEDeviceProtocol, timeout: float
    ) -> BLEClientProtocol:
        return bleak_client

    return _existing_client_factory

class UpliftDeskBluetoothCoordinator(DataUpdateCoordinator):
    """Define the Update Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: Uplift_Desk_DeskConfigEntry,
        desk_ble_device: BLEDevice
    ) -> None:
        """Initialize the Data Coordinator."""
        super().__init__(hass, _LOGGER, name="Uplift Desk", config_entry=config_entry)
        _LOGGER.debug("Initializing coordinator for desk %s:%s with config entry %s", config_entry.title, desk_ble_device.address, config_entry)

        self._discovered_desk = DiscoveredDesk(name=config_entry.title, address=desk_ble_device.address)
        self._desk_ble_device = desk_ble_device
        self._desk = None
        self.height_in: float | None = None

    async def _get_desk_controller(self):
        _LOGGER.debug("Getting desk controller for %s", self.desk_info)
        if self._desk is None or not self.is_connected:
            bleak_client = await establish_connection(
                BleakClientWithServiceCache,
                self._desk_ble_device,
                self._desk_ble_device.name or self.desk_name or "Unknown",
                max_attempts=3
            )

            bleak_client_factory: Callable[..., BLEClientProtocol] = _generate_existing_client_factory(bleak_client)

            validated_desk: DiscoveredDesk = await DeskValidator(bleak_client_factory).validate_device(self._discovered_desk, timeout=BLEAK_TIMEOUT_SECONDS)

            bleak_client = await establish_connection(
                BleakClientWithServiceCache,
                self._desk_ble_device,
                self._desk_ble_device.name or self.desk_name or "Unknown",
                max_attempts=3
            )
            self._desk = validated_desk.create_controller(bleak_client)
            self._desk.on(DeskEventType.HEIGHT, self._async_height_notify_callback)
            # Subscribe to notifications immediately so we capture the desk's
            # initial burst (height limits 0x07, current height 0x01, etc.)
            # that it sends right after a new BLE connection is established.
            await self._desk.start()
            _LOGGER.debug("Desk controller started for %s", self.desk_info)

        return self._desk

    @property
    def desk_name(self):
        return self._discovered_desk.name

    @property
    def desk_address(self):
        return self._discovered_desk.address

    @property
    def desk_info(self):
        return f"{self.desk_name} - {self.desk_address}"

    @property
    def is_connected(self):
        return self._desk is not None and self._desk.client is not None and self._desk.client.is_connected

    async def async_connect(self):
        await self._get_desk_controller()

    async def async_disconnect(self):
        controller = await self._get_desk_controller()
        await controller.stop()
        try:
            await controller.client.disconnect()
        finally:
            self._desk.client = None

    async def async_read_desk_height(self):
        controller = await self._get_desk_controller()
        await controller.request_height_limits()
        _LOGGER.debug(
            "After request_height_limits: height_mm=%s height_limit_config_max_mm=%s",
            controller.height_mm,
            controller.height_limit_config_max_mm,
        )
        if controller.height_mm is not None:
            self.height_in = convert_mm_to_in(controller.height_mm)
        return self.height_in

    async def async_preset_1(self):
        await self.async_wake()
        await (await self._get_desk_controller()).move_to_height_preset_1()

    async def async_preset_2(self):
        await self.async_wake()
        await (await self._get_desk_controller()).move_to_height_preset_2()

    async def async_wake(self):
        await (await self._get_desk_controller()).wake()

    async def async_move_to_max_height(self):
        controller = await self._get_desk_controller()
        max_height_mm = controller.height_limit_config_max_mm
        _LOGGER.debug("async_move_to_max_height: height_limit_config_max_mm=%s", max_height_mm)
        if not max_height_mm:
            await controller.request_height_limits()
            # command_writer already sleeps 1 s; allow extra time for desk response
            await asyncio.sleep(1.0)
            max_height_mm = controller.height_limit_config_max_mm
            _LOGGER.debug("After request_height_limits: height_limit_config_max_mm=%s", max_height_mm)
        if max_height_mm:
            # move_to_specified_height takes tenths-of-mm; height_limit_config_max_mm is in mm
            _LOGGER.debug("Moving to max height: %d mm (%d tenths-mm)", max_height_mm, max_height_mm * 10)
            await controller.move_to_specified_height(int(max_height_mm * 10))
        else:
            # Desk never reported height limits; send an over-large value and
            # rely on Jiecang firmware to clamp to its configured maximum.
            _LOGGER.warning(
                "Height limits not available from desk; commanding 0xFFFF tenths-mm "
                "and relying on firmware to clamp to configured maximum"
            )
            await controller.move_to_specified_height(_MAX_HEIGHT_TENTHS_MM_FALLBACK)

    async def async_stop(self):
        await (await self._get_desk_controller()).stop_movement()

    def _async_height_notify_callback(self, height_raw):
        stack = ''.join(traceback.format_stack(limit=6))
        _LOGGER.warning(
            "HEIGHT callback raw=%.4g  if_mm=%.2f\"  if_tenths=%.2f\"\nStack:\n%s",
            height_raw,
            height_raw / 25.4,
            height_raw / 254.0,
            stack,
        )
        self.height_in = convert_mm_to_in(height_raw)
        self.async_set_updated_data(self._desk)
