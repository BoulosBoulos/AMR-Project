"""Pure mission-planning helpers for the AMR final project.

Status: UNVERIFIED ON JAZZY/HARMONIC.

This module intentionally has no ROS 2, Nav2, Gazebo, or file-system
dependencies. It only owns the exact mission strings and waypoint-name logic
from the project handoff.
"""

from __future__ import annotations


SERVICE_LOCATIONS = {
    "GROCERY": "supermarket",
    "FOOD": "restaurant",
    "FIRE": "firefighting_center",
    "MEDICAL": "pharmacy",
}

VALID_HOUSES = frozenset(
    {
        "house_1",
        "house_2",
        "house_3",
        "house_4",
        "house_5",
    }
)

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

DOCKING_STATION = "docking_station"


class MissionValidationError(ValueError):
    """Raised when a mission request does not match the locked project spec."""


def validate_mission(mission_type: str, target_house: str) -> None:
    """Validate mission fields against the exact locked string sets.

    Args:
        mission_type: One of GROCERY, FOOD, FIRE, MEDICAL.
        target_house: One of house_1 through house_5.

    Raises:
        MissionValidationError: If either field is invalid.
    """
    if mission_type not in SERVICE_LOCATIONS:
        valid = ", ".join(sorted(SERVICE_LOCATIONS))
        raise MissionValidationError(
            f"Invalid mission_type {mission_type!r}; expected one of: {valid}"
        )

    if target_house not in VALID_HOUSES:
        valid = ", ".join(sorted(VALID_HOUSES))
        raise MissionValidationError(
            f"Invalid target_house {target_house!r}; expected one of: {valid}"
        )


def build_waypoint_names(mission_type: str, target_house: str) -> list[str]:
    """Build executable waypoint names for a mission.

    The service robot is assumed to begin at the dock. The commanded Nav2
    waypoint sequence is therefore service location, target house, then dock.
    """
    validate_mission(mission_type, target_house)
    return [
        SERVICE_LOCATIONS[mission_type],
        target_house,
        DOCKING_STATION,
    ]


def missing_required_landmarks(landmark_names: set[str]) -> set[str]:
    """Return required landmark names that are absent from a landmark set."""
    return REQUIRED_LANDMARKS - landmark_names
