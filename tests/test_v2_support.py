"""Unit tests for V2-specific Uplift desk support."""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PREFIXES = (
    "custom_components.uplift_desk",
    "homeassistant",
    "bleak",
    "bleak_retry_connector",
    "uplift_ble",
    "voluptuous",
)


def _purge_test_modules() -> None:
    """Remove cached modules so each test gets a clean import surface."""
    for name in list(sys.modules):
        if name == "custom_components" or name.startswith(MODULE_PREFIXES):
            sys.modules.pop(name, None)


def _install_stub_modules() -> None:
    """Install minimal stubs so the integration can be imported without HA."""
    _purge_test_modules()

    def add_module(name: str) -> ModuleType:
        module = ModuleType(name)
        sys.modules[name] = module
        return module

    voluptuous = add_module("voluptuous")
    voluptuous.Schema = lambda value: value
    voluptuous.Required = lambda value, default=None: value
    voluptuous.Optional = lambda value, default=None: value

    homeassistant = add_module("homeassistant")
    homeassistant.__path__ = []

    components = add_module("homeassistant.components")
    components.__path__ = []
    homeassistant.components = components

    bluetooth = add_module("homeassistant.components.bluetooth")
    components.bluetooth = bluetooth

    class BluetoothServiceInfoBleak:
        """Simple Bluetooth discovery payload."""

        def __init__(self, address: str, name: str | None = None) -> None:
            self.address = address
            self.name = name

    bluetooth.BluetoothServiceInfoBleak = BluetoothServiceInfoBleak
    bluetooth.async_ble_device_from_address = lambda hass, address: None

    button = add_module("homeassistant.components.button")
    components.button = button

    class ButtonEntity:
        """Stub button entity."""

    class ButtonEntityDescription:
        """Stub button description."""

        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)

    button.ButtonEntity = ButtonEntity
    button.ButtonEntityDescription = ButtonEntityDescription

    sensor = add_module("homeassistant.components.sensor")
    components.sensor = sensor

    class SensorEntity:
        """Stub sensor entity."""

    class SensorEntityDescription:
        """Stub sensor description."""

        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)

    class SensorDeviceClass:
        DISTANCE = "distance"

    class SensorStateClass:
        MEASUREMENT = "measurement"

    sensor.SensorEntity = SensorEntity
    sensor.SensorEntityDescription = SensorEntityDescription
    sensor.SensorDeviceClass = SensorDeviceClass
    sensor.SensorStateClass = SensorStateClass

    config_entries = add_module("homeassistant.config_entries")
    homeassistant.config_entries = config_entries

    class ConfigEntry:
        """Stub config entry type."""

        def __class_getitem__(cls, item):
            return cls

    class ConfigFlow:
        """Stub config flow base class."""

        def __init_subclass__(cls, **kwargs) -> None:
            super().__init_subclass__()

        def __new__(cls, *args, **kwargs):
            instance = super().__new__(cls)
            instance.context = {}
            instance._unique_id = None
            instance.confirm_only = False
            return instance

        def __init__(self) -> None:
            return None

        async def async_set_unique_id(self, unique_id: str) -> None:
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self) -> None:
            return None

        def _set_confirm_only(self) -> None:
            self.confirm_only = True

        def async_show_form(
            self,
            *,
            step_id: str,
            data_schema=None,
            errors=None,
            description_placeholders=None,
        ) -> dict[str, object]:
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
                "description_placeholders": description_placeholders,
            }

        def async_create_entry(self, *, title: str, data: dict[str, object]):
            return {"type": "create_entry", "title": title, "data": data}

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.ConfigFlowResult = dict

    const = add_module("homeassistant.const")
    homeassistant.const = const
    const.CONF_ADDRESS = "address"
    const.CONF_NAME = "name"

    class Platform:
        SENSOR = "sensor"
        BUTTON = "button"

    class UnitOfLength:
        INCHES = "in"

    const.Platform = Platform
    const.UnitOfLength = UnitOfLength

    core = add_module("homeassistant.core")
    homeassistant.core = core

    class HomeAssistant:
        """Stub Home Assistant core object."""

    def callback(func):
        return func

    core.HomeAssistant = HomeAssistant
    core.callback = callback

    exceptions = add_module("homeassistant.exceptions")
    homeassistant.exceptions = exceptions

    class ConfigEntryNotReady(Exception):
        """Stub setup retry exception."""

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args)
            self.kwargs = kwargs

    exceptions.ConfigEntryNotReady = ConfigEntryNotReady

    helpers = add_module("homeassistant.helpers")
    helpers.__path__ = []
    homeassistant.helpers = helpers

    config_validation = add_module("homeassistant.helpers.config_validation")
    config_validation.string = str
    helpers.config_validation = config_validation

    entity_platform = add_module("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = list
    helpers.entity_platform = entity_platform

    update_coordinator = add_module("homeassistant.helpers.update_coordinator")
    helpers.update_coordinator = update_coordinator

    class DataUpdateCoordinator:
        """Stub data update coordinator."""

        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, logger, name=None, config_entry=None) -> None:
            self.hass = hass
            self.logger = logger
            self.name = name
            self.config_entry = config_entry
            self.data = None

        def async_set_updated_data(self, data) -> None:
            self.data = data

    class CoordinatorEntity:
        """Stub coordinator entity."""

        def __class_getitem__(cls, item):
            return cls

        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.CoordinatorEntity = CoordinatorEntity

    bleak = add_module("bleak")

    class BleakClient:
        """Stub Bleak client."""

    bleak.BleakClient = BleakClient

    bleak_backends = add_module("bleak.backends")
    bleak_backends.__path__ = []

    bleak_device = add_module("bleak.backends.device")

    class BLEDevice:
        """Stub BLE device."""

        def __init__(self, address: str, name: str | None = None) -> None:
            self.address = address
            self.name = name

    bleak_device.BLEDevice = BLEDevice

    bleak_retry_connector = add_module("bleak_retry_connector")

    class BleakClientWithServiceCache:
        """Stub Bleak client with cache."""

    async def establish_connection(*args, **kwargs):
        raise AssertionError("establish_connection should be stubbed per test")

    bleak_retry_connector.BleakClientWithServiceCache = BleakClientWithServiceCache
    bleak_retry_connector.establish_connection = establish_connection

    uplift_ble = add_module("uplift_ble")
    uplift_ble.__path__ = []

    ble_protos = add_module("uplift_ble.ble_protos")
    uplift_ble.ble_protos = ble_protos

    class BLEClientProtocol:
        """Stub client protocol."""

    class BLEDeviceProtocol:
        """Stub device protocol."""

    ble_protos.BLEClientProtocol = BLEClientProtocol
    ble_protos.BLEDeviceProtocol = BLEDeviceProtocol

    desk_controller = add_module("uplift_ble.desk_controller")
    uplift_ble.desk_controller = desk_controller

    class DeskController:
        """Stub desk controller."""

    desk_controller.DeskController = DeskController

    desk_enums = add_module("uplift_ble.desk_enums")
    uplift_ble.desk_enums = desk_enums

    class DeskEventType:
        HEIGHT = "height"

    desk_enums.DeskEventType = DeskEventType

    desk_validator = add_module("uplift_ble.desk_validator")
    uplift_ble.desk_validator = desk_validator

    class DeskValidator:
        """Stub desk validator."""

        def __init__(self, client_factory=None) -> None:
            self.client_factory = client_factory

        async def validate_device(self, device, timeout=0):
            return None

    desk_validator.DeskValidator = DeskValidator

    models = add_module("uplift_ble.models")
    uplift_ble.models = models

    class DiscoveredDesk:
        """Stub discovered desk model."""

        def __init__(self, address: str, name: str | None, desk_config=None) -> None:
            self.address = address
            self.name = name
            self.desk_config = desk_config

        def create_controller(self, client):
            return client

    models.DiscoveredDesk = DiscoveredDesk


def _load_integration_modules(*module_names: str) -> dict[str, ModuleType]:
    """Import the integration modules with stubbed dependencies."""
    _install_stub_modules()
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    importlib.invalidate_caches()

    imported = {
        "__init__": importlib.import_module("custom_components.uplift_desk"),
    }
    for module_name in module_names:
        imported[module_name] = importlib.import_module(
            f"custom_components.uplift_desk.{module_name}"
        )
    return imported


class V2SupportTestCase(unittest.TestCase):
    """Exercise the new V2 support without a Home Assistant runtime."""

    def tearDown(self) -> None:
        _purge_test_modules()

    def test_v2_modules_import_without_legacy_uplift_dependency(self) -> None:
        modules = _load_integration_modules(
            "button",
            "config_flow",
            "coordinator",
            "sensor",
        )
        self.assertIn("__init__", modules)
        self.assertIn("button", modules)
        self.assertIn("coordinator", modules)

    def test_manual_v2_address_creates_entry_with_normalized_address(self) -> None:
        modules = _load_integration_modules("config_flow")
        flow = modules["config_flow"].UpliftDeskConfigFlow()

        result = asyncio.run(
            flow.async_step_user({"address": "f0-ae-7d-75-b2-05", "name": ""})
        )

        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["title"], "Uplift Desk 75B205")
        self.assertEqual(result["data"]["address"], "F0:AE:7D:75:B2:05")
        self.assertEqual(result["data"]["name"], "Uplift Desk 75B205")

    def test_invalid_manual_v2_address_returns_field_error(self) -> None:
        modules = _load_integration_modules("config_flow")
        flow = modules["config_flow"].UpliftDeskConfigFlow()

        result = asyncio.run(
            flow.async_step_user({"address": "not-a-mac", "name": "Desk"})
        )

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {"address": "invalid_address"})

    def test_bluetooth_discovery_confirm_uses_normalized_v2_address(self) -> None:
        modules = _load_integration_modules("config_flow")
        bluetooth = sys.modules["homeassistant.components.bluetooth"]
        flow = modules["config_flow"].UpliftDeskConfigFlow()
        discovery_info = bluetooth.BluetoothServiceInfoBleak(
            address="f0-ae-7d-75-b2-05",
            name="Office Desk",
        )

        form_result = asyncio.run(flow.async_step_bluetooth(discovery_info))
        create_result = asyncio.run(flow.async_step_bluetooth_confirm({"confirm": True}))

        self.assertEqual(form_result["type"], "form")
        self.assertEqual(form_result["step_id"], "bluetooth_confirm")
        self.assertEqual(
            form_result["description_placeholders"],
            {"name": "Office Desk"},
        )
        self.assertEqual(create_result["type"], "create_entry")
        self.assertEqual(create_result["data"]["address"], "F0:AE:7D:75:B2:05")
        self.assertEqual(create_result["data"]["name"], "Office Desk")

    def test_move_to_max_prefers_live_limit_for_v2_desk(self) -> None:
        modules = _load_integration_modules("coordinator")
        coordinator_module = modules["coordinator"]
        entry = SimpleNamespace(title="Uplift Desk 75B205")
        device = SimpleNamespace(address="F0:AE:7D:75:B2:05", name="Office Desk")
        coordinator = coordinator_module.UpliftDeskBluetoothCoordinator(
            hass=object(),
            config_entry=entry,
            desk_ble_device=device,
        )

        class FakeDesk:
            def __init__(self) -> None:
                self.height_limit_max_mm = 1300
                self.height_limit_config_max_mm = 1270
                self.moves: list[int] = []

            async def move_to_specified_height(self, height: int) -> None:
                self.moves.append(height)

        fake_desk = FakeDesk()

        async def fake_get_desk_controller():
            return fake_desk

        coordinator._get_desk_controller = fake_get_desk_controller

        asyncio.run(coordinator.async_move_to_max())

        self.assertEqual(fake_desk.moves, [1300])

    def test_move_to_max_requests_limits_when_missing(self) -> None:
        modules = _load_integration_modules("coordinator")
        coordinator_module = modules["coordinator"]
        entry = SimpleNamespace(title="Uplift Desk 75B205")
        device = SimpleNamespace(address="F0:AE:7D:75:B2:05", name="Office Desk")
        coordinator = coordinator_module.UpliftDeskBluetoothCoordinator(
            hass=object(),
            config_entry=entry,
            desk_ble_device=device,
        )

        class FakeDesk:
            def __init__(self) -> None:
                self.height_limit_max_mm = None
                self.height_limit_config_max_mm = 0
                self.moves: list[int] = []
                self.requested_limits = 0

            async def request_height_limits(self) -> None:
                self.requested_limits += 1
                self.height_limit_config_max_mm = 1270

            async def move_to_specified_height(self, height: int) -> None:
                self.moves.append(height)

        fake_desk = FakeDesk()

        async def fake_get_desk_controller():
            return fake_desk

        coordinator._get_desk_controller = fake_get_desk_controller

        asyncio.run(coordinator.async_move_to_max())

        self.assertEqual(fake_desk.requested_limits, 1)
        self.assertEqual(fake_desk.moves, [1270])

    def test_move_to_max_raises_without_reported_limit(self) -> None:
        modules = _load_integration_modules("coordinator")
        coordinator_module = modules["coordinator"]
        entry = SimpleNamespace(title="Uplift Desk 75B205")
        device = SimpleNamespace(address="F0:AE:7D:75:B2:05", name="Office Desk")
        coordinator = coordinator_module.UpliftDeskBluetoothCoordinator(
            hass=object(),
            config_entry=entry,
            desk_ble_device=device,
        )

        class FakeDesk:
            def __init__(self) -> None:
                self.height_limit_max_mm = None
                self.height_limit_config_max_mm = 0
                self.moves: list[int] = []
                self.requested_limits = 0

            async def request_height_limits(self) -> None:
                self.requested_limits += 1

            async def move_to_specified_height(self, height: int) -> None:
                self.moves.append(height)

        fake_desk = FakeDesk()

        async def fake_get_desk_controller():
            return fake_desk

        coordinator._get_desk_controller = fake_get_desk_controller

        with self.assertRaisesRegex(RuntimeError, "usable maximum height"):
            asyncio.run(coordinator.async_move_to_max())

        self.assertEqual(fake_desk.requested_limits, 1)
        self.assertEqual(fake_desk.moves, [])

    def test_height_notification_converts_v2_mm_updates_to_inches(self) -> None:
        modules = _load_integration_modules("coordinator")
        coordinator_module = modules["coordinator"]
        entry = SimpleNamespace(title="Uplift Desk 75B205")
        device = SimpleNamespace(address="F0:AE:7D:75:B2:05", name="Office Desk")
        coordinator = coordinator_module.UpliftDeskBluetoothCoordinator(
            hass=object(),
            config_entry=entry,
            desk_ble_device=device,
        )

        coordinator._async_height_notify_callback(1016.0)

        self.assertAlmostEqual(coordinator.height_in, 40.0)
        self.assertAlmostEqual(coordinator.data, 40.0)

    def test_coordinator_connect_uses_plain_bleak_client_for_v2_desk(self) -> None:
        modules = _load_integration_modules("coordinator")
        coordinator_module = modules["coordinator"]
        bleak_module = sys.modules["bleak"]
        entry = SimpleNamespace(title="Uplift Desk 75B205")
        device = SimpleNamespace(address="F0:AE:7D:75:B2:05", name="Office Desk")
        coordinator = coordinator_module.UpliftDeskBluetoothCoordinator(
            hass=object(),
            config_entry=entry,
            desk_ble_device=device,
        )

        class FakeDeskController:
            def __init__(self) -> None:
                self.client = SimpleNamespace(is_connected=True)

            def on(self, event_type, callback) -> None:
                self.event_type = event_type
                self.callback = callback

        class FakeDiscoveredDesk:
            def create_controller(self, client):
                self.client = client
                return FakeDeskController()

        class FakeValidator:
            def __init__(self, client_factory=None) -> None:
                self.client_factory = client_factory

            async def validate_device(self, desk_device, timeout=0):
                return FakeDiscoveredDesk()

        establish_calls: list[tuple[object, dict[str, object]]] = []

        async def fake_establish_connection(client_cls, *args, **kwargs):
            establish_calls.append((client_cls, kwargs))
            return SimpleNamespace(is_connected=True)

        coordinator_module.DeskValidator = FakeValidator
        coordinator_module.establish_connection = fake_establish_connection

        desk = asyncio.run(coordinator._get_desk_controller())

        self.assertEqual(len(establish_calls), 2)
        self.assertEqual(
            [client_cls for client_cls, _ in establish_calls],
            [bleak_module.BleakClient, bleak_module.BleakClient],
        )
        self.assertEqual(
            [kwargs["use_services_cache"] for _, kwargs in establish_calls],
            [False, False],
        )
        self.assertTrue(desk.client.is_connected)

    def test_async_setup_entry_allows_initial_height_timeout(self) -> None:
        modules = _load_integration_modules()
        bluetooth = sys.modules["homeassistant.components.bluetooth"]
        bluetooth.async_ble_device_from_address = lambda hass, address: SimpleNamespace(
            address=address,
            name="Office Desk",
        )
        modules["__init__"].async_ble_device_from_address = (
            bluetooth.async_ble_device_from_address
        )

        class FakeCoordinator:
            def __init__(self, hass, entry, ble_device) -> None:
                self.hass = hass
                self.entry = entry
                self.ble_device = ble_device
                self.connect_calls = 0
                self.read_calls = 0
                self.disconnect_calls = 0

            async def async_connect(self) -> None:
                self.connect_calls += 1

            async def async_read_desk_height(self) -> None:
                self.read_calls += 1
                raise TimeoutError

            async def async_disconnect(self) -> None:
                self.disconnect_calls += 1

        class FakeConfigEntries:
            def __init__(self) -> None:
                self.forward_calls: list[tuple[object, list[str]]] = []

            async def async_forward_entry_setups(self, entry, platforms) -> None:
                self.forward_calls.append((entry, list(platforms)))

        config_entries = FakeConfigEntries()
        hass = SimpleNamespace(config_entries=config_entries)
        entry = SimpleNamespace(
            data={"address": "F0:AE:7D:75:B2:05"},
            title="Uplift Desk 75B205",
            runtime_data=None,
        )

        modules["__init__"].UpliftDeskBluetoothCoordinator = FakeCoordinator

        result = asyncio.run(modules["__init__"].async_setup_entry(hass, entry))

        self.assertTrue(result)
        self.assertIsInstance(entry.runtime_data, FakeCoordinator)
        self.assertEqual(entry.runtime_data.connect_calls, 1)
        self.assertEqual(entry.runtime_data.read_calls, 1)
        self.assertEqual(entry.runtime_data.disconnect_calls, 0)
        self.assertEqual(len(config_entries.forward_calls), 1)

    def test_async_setup_entry_retries_when_connect_times_out(self) -> None:
        modules = _load_integration_modules()
        bluetooth = sys.modules["homeassistant.components.bluetooth"]
        bluetooth.async_ble_device_from_address = lambda hass, address: SimpleNamespace(
            address=address,
            name="Office Desk",
        )
        modules["__init__"].async_ble_device_from_address = (
            bluetooth.async_ble_device_from_address
        )
        modules["__init__"].BLEAK_TIMEOUT_SECONDS = 0.01
        config_entry_not_ready = sys.modules[
            "homeassistant.exceptions"
        ].ConfigEntryNotReady

        class FakeCoordinator:
            def __init__(self, hass, entry, ble_device) -> None:
                self.disconnect_calls = 0

            async def async_connect(self) -> None:
                await asyncio.sleep(0.1)

            async def async_read_desk_height(self) -> None:
                raise AssertionError("height read should not run after connect timeout")

            async def async_disconnect(self) -> None:
                self.disconnect_calls += 1

        class FakeConfigEntries:
            def __init__(self) -> None:
                self.forward_calls: list[tuple[object, list[str]]] = []

            async def async_forward_entry_setups(self, entry, platforms) -> None:
                self.forward_calls.append((entry, list(platforms)))

        config_entries = FakeConfigEntries()
        hass = SimpleNamespace(config_entries=config_entries)
        entry = SimpleNamespace(
            data={"address": "F0:AE:7D:75:B2:05"},
            title="Uplift Desk 75B205",
            runtime_data=None,
        )

        modules["__init__"].UpliftDeskBluetoothCoordinator = FakeCoordinator

        with self.assertRaises(config_entry_not_ready):
            asyncio.run(modules["__init__"].async_setup_entry(hass, entry))

        self.assertIsInstance(entry.runtime_data, FakeCoordinator)
        self.assertEqual(entry.runtime_data.disconnect_calls, 1)
        self.assertEqual(config_entries.forward_calls, [])
