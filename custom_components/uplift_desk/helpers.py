"""Helper utilities for the Uplift Desk integration."""

from __future__ import annotations

import re

DEFAULT_MAX_HEIGHT_MM = 1293

_ADDRESS_RE = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")


def normalize_bluetooth_address(address: str) -> str:
    """Normalize a user-supplied Bluetooth MAC address."""
    return address.strip().replace("-", ":").upper()


def is_valid_bluetooth_address(address: str) -> bool:
    """Return whether the supplied address is a valid Bluetooth MAC."""
    return bool(_ADDRESS_RE.fullmatch(normalize_bluetooth_address(address)))


def default_desk_name(address: str) -> str:
    """Build a stable fallback desk name from the Bluetooth address."""
    suffix = normalize_bluetooth_address(address).replace(":", "")[-6:]
    return f"Uplift Desk {suffix}"


def desk_title(name: str | None, address: str) -> str:
    """Choose the best display title for a desk."""
    if name and name.strip():
        return name.strip()
    return default_desk_name(address)


def choose_max_height_mm(*candidates: int | float | None) -> int:
    """Select a usable maximum height, falling back to the measured desk max."""
    for candidate in candidates:
        if candidate is None:
            continue
        value = int(candidate)
        if value > 0:
            return value
    return DEFAULT_MAX_HEIGHT_MM
