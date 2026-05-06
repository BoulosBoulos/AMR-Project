"""Landmark database loading and validation helpers.

Status: UNVERIFIED ON JAZZY/HARMONIC.

This module is pure Python. It validates the YAML shape expected from the QR
landmark-detection pipeline without depending on ROS 2, Nav2, Gazebo, or TF.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import yaml


REQUIRED_LANDMARKS = frozenset(
    {
        "pharmacy",
        "firefighting_center",
        "supermarket",
        "restaurant",
        "house_1",
        "house_2",
        "house_3",
        "house_4",
        "house_5",
        "docking_station",
    }
)


class LandmarkDatabaseError(ValueError):
    """Raised when a landmark database cannot be used safely."""


@dataclass(frozen=True)
class Landmark:
    """A named 2D landmark pose in the map frame."""

    name: str
    x: float
    y: float


def load_landmarks_yaml(path: str | Path) -> dict[str, Landmark]:
    """Load and validate landmarks from a YAML file."""
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)

    return parse_landmarks(data)


def parse_landmarks(data: Any) -> dict[str, Landmark]:
    """Parse a loaded YAML object into a validated landmark dictionary.

    Expected format:

    .. code-block:: yaml

       landmarks:
         pharmacy: {x: -5.42, y: 3.18}
         docking_station: {x: 0.0, y: 0.0}
    """
    if not isinstance(data, dict):
        raise LandmarkDatabaseError("Landmark YAML must contain a mapping")

    raw_landmarks = data.get("landmarks")
    if not isinstance(raw_landmarks, dict):
        raise LandmarkDatabaseError(
            "Landmark YAML must contain a 'landmarks' mapping"
        )

    missing = REQUIRED_LANDMARKS - set(raw_landmarks)
    if missing:
        names = ", ".join(sorted(missing))
        raise LandmarkDatabaseError(f"Missing required landmarks: {names}")

    landmarks = {}
    for name, raw_pose in raw_landmarks.items():
        if not isinstance(raw_pose, dict):
            raise LandmarkDatabaseError(
                f"Landmark {name!r} must map to x/y values"
            )
        landmarks[name] = Landmark(
            name=name,
            x=_read_float(raw_pose, "x", name),
            y=_read_float(raw_pose, "y", name),
        )

    return landmarks


def get_landmark(landmarks: dict[str, Landmark], name: str) -> Landmark:
    """Return one landmark or raise a useful validation error."""
    try:
        return landmarks[name]
    except KeyError as exc:
        raise LandmarkDatabaseError(f"Unknown landmark {name!r}") from exc


def _read_float(raw_pose: dict[str, Any], key: str, name: str) -> float:
    """Read one finite coordinate from a raw landmark pose."""
    if key not in raw_pose:
        raise LandmarkDatabaseError(f"Landmark {name!r} is missing '{key}'")

    value = raw_pose[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LandmarkDatabaseError(
            f"Landmark {name!r} field '{key}' must be numeric"
        )

    coordinate = float(value)
    if not math.isfinite(coordinate):
        raise LandmarkDatabaseError(
            f"Landmark {name!r} field '{key}' must be finite"
        )

    return coordinate
