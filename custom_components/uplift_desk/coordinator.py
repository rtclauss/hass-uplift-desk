"""Coordinator for the Uplift Desk integration."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import TYPE_CHECKING

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from uplift_ble.ble_protos import BLEClientProtocol, BLEDeviceProtocol
from uplift_ble.desk_controller import DeskController
from uplift_ble.desk_enums import DeskEventType
from uplift_ble.desk_validator import DeskValidator
from uplift_ble.models import DiscoveredDesk

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import BLEAK_TIMEOUT_SECONDS
from .helpers import choose_max_height_mm, desk_title

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

type Uplift_Desk_DeskConfigEntry = ConfigEntry["UpliftDeskBluetoothCoordinator"]


_LOGGER = logging.getLogger(__name__)


def convert_mm_to_in(millimeters: int | float) -> float:
    """Convert millimeters to inches."""
    return millimeters / 25.4


def _generate_existing_client_factory(
    bleak_client: BleakClient,
) -> Callable[..., BLEClientProtocol]:
    def _existing_client_factory(
        device: BLEDeviceProtocol, timeout: float
    ) -> BLEClientProtocol:
        return bleak_client

    return _existing_client_factory


class UpliftDeskBluetoothCoordinator(DataUpdateCoordinator[float | None]):
    """Coordinate Bluetooth I/O and desk state."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: Uplift_Desk_DeskConfigEntry,
        desk_ble_device: BLEDevice,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name="Uplift Desk", config_entry=config_entry)
        self._entry = config_entry
        self._desk_ble_device = desk_ble_device
        self._discovered_desk: DiscoveredDesk | None = None
        self._desk: DeskController | None = None
        self.height_in: float | None = None

    @property
    def desk_name(self) -> str:
        """Return the configured desk name."""
        return desk_title(self._entry.title, self._desk_ble_device.address)

    @property
    def desk_address(self) -> str:
        """Return the Bluetooth address."""
        return self._desk_ble_device.address

    @property
    def desk_info(self) -> str:
        """Return a concise desk identifier."""
        return f"{self.desk_name} - {self.desk_address}"

    @property
    def is_connected(self) -> bool:
        """Return whether the underlying BLE client is connected."""
        return (
            self._desk is not None
            and self._desk.client is not None
            and self._desk.client.is_connected
        )

    async def _get_desk_controller(self) -> DeskController:
        """Return a validated, connected desk controller."""
        if self._desk is not None and self.is_connected:
            return self._desk

        validation_client = await establish_connection(
            BleakClient,
            self._desk_ble_device,
            self._desk_ble_device.name or self.desk_name,
            max_attempts=3,
            use_services_cache=False,
        )

        validator = DeskValidator(
            client_factory=_generate_existing_client_factory(validation_client)
        )
        validated_desk = await validator.validate_device(
            self._desk_ble_device, timeout=BLEAK_TIMEOUT_SECONDS
        )
        if validated_desk is None:
            raise RuntimeError(
                f"Failed to validate desk at {self._desk_ble_device.address}"
            )

        desk_client = await establish_connection(
            BleakClient,
            self._desk_ble_device,
            self._desk_ble_device.name or self.desk_name,
            max_attempts=3,
            use_services_cache=False,
        )
        self._discovered_desk = validated_desk
        self._desk = validated_desk.create_controller(desk_client)
        self._desk.on(DeskEventType.HEIGHT, self._async_height_notify_callback)
        return self._desk

    async def async_connect(self) -> None:
        """Start the BLE controller."""
        await (await self._get_desk_controller()).start()

    async def async_disconnect(self) -> None:
        """Stop notifications and disconnect cleanly."""
        if self._desk is None:
            return

        try:
            await self._desk.stop()
        finally:
            if self._desk.client is not None and self._desk.client.is_connected:
                await self._desk.client.disconnect()
            self._desk = None

    async def async_read_desk_height(self) -> float | None:
        """Request desk telemetry and update the cached height."""
        desk = await self._get_desk_controller()
        await desk.request_height_limits()
        if desk.height_mm is not None:
            self.height_in = convert_mm_to_in(desk.height_mm)
            self.async_set_updated_data(self.height_in)
        return self.height_in

    async def async_preset_1(self) -> None:
        """Move the desk to preset 1."""
        await (await self._get_desk_controller()).move_to_height_preset_1()

    async def async_preset_2(self) -> None:
        """Move the desk to preset 2."""
        await (await self._get_desk_controller()).move_to_height_preset_2()

    async def async_move_to_max(self) -> None:
        """Move the desk to its configured maximum height."""
        desk = await self._get_desk_controller()
        max_height_mm = choose_max_height_mm(
            desk.height_limit_max_mm,
            desk.height_limit_config_max_mm,
        )
        if max_height_mm is None:
            await desk.request_height_limits()
            max_height_mm = choose_max_height_mm(
                desk.height_limit_max_mm,
                desk.height_limit_config_max_mm,
            )
        if max_height_mm is None:
            raise RuntimeError(
                f"Desk {self.desk_info} did not report a usable maximum height"
            )
        await desk.move_to_specified_height(max_height_mm)

    async def async_stop(self) -> None:
        """Stop desk movement."""
        await (await self._get_desk_controller()).stop_movement()

    def _async_height_notify_callback(self, height_mm: float) -> None:
        """Handle height notifications from the desk."""
        self.height_in = convert_mm_to_in(height_mm)
        self.async_set_updated_data(self.height_in)
