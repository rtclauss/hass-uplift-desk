"""Tests for helper utilities."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


HELPERS_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "uplift_desk"
    / "helpers.py"
)
SPEC = spec_from_file_location("uplift_desk_helpers", HELPERS_PATH)
assert SPEC is not None and SPEC.loader is not None
HELPERS = module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERS)


class HelpersTestCase(unittest.TestCase):
    """Exercise the pure helper functions without importing Home Assistant."""

    def test_normalize_bluetooth_address(self) -> None:
        self.assertEqual(
            HELPERS.normalize_bluetooth_address("f0-ae-7d-75-b2-05"),
            "F0:AE:7D:75:B2:05",
        )

    def test_is_valid_bluetooth_address(self) -> None:
        self.assertTrue(HELPERS.is_valid_bluetooth_address("F0:AE:7D:75:B2:05"))
        self.assertFalse(HELPERS.is_valid_bluetooth_address("bad-address"))

    def test_default_desk_name_uses_suffix(self) -> None:
        self.assertEqual(
            HELPERS.default_desk_name("F0:AE:7D:75:B2:05"),
            "Uplift Desk 75B205",
        )

    def test_choose_max_height_mm_prefers_first_positive_value(self) -> None:
        self.assertEqual(
            HELPERS.choose_max_height_mm(None, 1234, 1270),
            1234,
        )
        self.assertEqual(
            HELPERS.choose_max_height_mm(1200, 1234, 1270),
            1200,
        )
        self.assertIsNone(
            HELPERS.choose_max_height_mm(None, 0, None),
        )


if __name__ == "__main__":
    unittest.main()
