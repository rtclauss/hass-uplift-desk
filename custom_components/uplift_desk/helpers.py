"""Helper utilities for the Uplift Desk integration."""

from __future__ import annotations

import re

DEFAULT_MIN_HEIGHT_MM = 643
DEFAULT_MAX_HEIGHT_MM = 1293
POSITION_ENCODED_HEIGHT_LOW_BYTE = 0x0F
POSITION_ENCODED_HEIGHT_ZERO_BYTE = 0xFD
POSITION_ENCODED_HEIGHT_STEPS = 255

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


def choose_height_limit_mm(*candidates: int | float | None) -> int | None:
    """Select the first positive height limit value."""
    for candidate in candidates:
        if candidate is None:
            continue
        value = int(candidate)
        if value > 0:
            return value
    return None


def decode_position_encoded_height_mm(
    raw_height_mm: int | float,
    minimum_height_mm: int | float,
    maximum_height_mm: int | float,
) -> float:
    """Decode the V2 position-encoded height notification into millimeters.

    Some V2 desks expose current height as a wrapping one-byte position value
    rather than an absolute height in tenths of millimeters. The byte sequence
    observed on this desk is ``[position, 0x0F]``, where position wraps from
    ``0xFF`` back to ``0x00`` as the desk rises.
    """
    raw_tenths_mm = int(round(float(raw_height_mm) * 10))
    position_byte = raw_tenths_mm >> 8
    position_offset = (
        position_byte - POSITION_ENCODED_HEIGHT_ZERO_BYTE
    ) % (POSITION_ENCODED_HEIGHT_STEPS + 1)
    span_mm = float(maximum_height_mm) - float(minimum_height_mm)
    return float(minimum_height_mm) + (
        position_offset / POSITION_ENCODED_HEIGHT_STEPS
    ) * span_mm
