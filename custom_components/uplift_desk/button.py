"""Platform for button integration."""
from __future__ import annotations
import logging

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Uplift_Desk_DeskConfigEntry
from .coordinator import UpliftDeskBluetoothCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: Uplift_Desk_DeskConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    _LOGGER.debug("Setting up button platform for desk %s", config_entry.runtime_data.desk_info)
    async_add_entities([
        UpliftDeskPreset1Button(config_entry.runtime_data),
        UpliftDeskPreset2Button(config_entry.runtime_data),
        UpliftDeskMaxHeightButton(config_entry.runtime_data),
        UpliftDeskStopButton(config_entry.runtime_data),
    ])

class UpliftDeskPreset1Button(CoordinatorEntity[UpliftDeskBluetoothCoordinator], ButtonEntity):
    entity_description = ButtonEntityDescription(key="desk_preset_1", translation_key="desk_preset_1", has_entity_name=True)
    def __init__(self, coordinator: UpliftDeskBluetoothCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.desk_address}_{self.entity_description.key}"
    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.desk_address)}, "name": self.coordinator.desk_name}
    async def async_press(self) -> None:
        await self.coordinator.async_preset_1()

class UpliftDeskPreset2Button(CoordinatorEntity[UpliftDeskBluetoothCoordinator], ButtonEntity):
    entity_description = ButtonEntityDescription(key="desk_preset_2", translation_key="desk_preset_2", has_entity_name=True)
    def __init__(self, coordinator: UpliftDeskBluetoothCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.desk_address}_{self.entity_description.key}"
    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.desk_address)}, "name": self.coordinator.desk_name}
    async def async_press(self) -> None:
        await self.coordinator.async_preset_2()

class UpliftDeskMaxHeightButton(CoordinatorEntity[UpliftDeskBluetoothCoordinator], ButtonEntity):
    entity_description = ButtonEntityDescription(key="desk_max", translation_key="desk_max", has_entity_name=True)
    def __init__(self, coordinator: UpliftDeskBluetoothCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.desk_address}_{self.entity_description.key}"
    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.desk_address)}, "name": self.coordinator.desk_name}
    async def async_press(self) -> None:
        await self.coordinator.async_move_to_max_height()

class UpliftDeskStopButton(CoordinatorEntity[UpliftDeskBluetoothCoordinator], ButtonEntity):
    entity_description = ButtonEntityDescription(key="desk_stop", translation_key="desk_stop", has_entity_name=True)
    def __init__(self, coordinator: UpliftDeskBluetoothCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.desk_address}_{self.entity_description.key}"
    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.desk_address)}, "name": self.coordinator.desk_name}
    async def async_press(self) -> None:
        await self.coordinator.async_stop()
