"""Tests for portable mission logic."""

import pytest

from amr_mission.mission_logic import (
    DOCKING_STATION,
    REQUIRED_LANDMARKS,
    SERVICE_LOCATIONS,
    VALID_HOUSES,
    MissionValidationError,
    build_waypoint_names,
    missing_required_landmarks,
    validate_mission,
)


def test_locked_mission_mapping():
    """Mission types map to the exact required service landmarks."""
    assert SERVICE_LOCATIONS == {
        "GROCERY": "supermarket",
        "FOOD": "restaurant",
        "FIRE": "firefighting_center",
        "MEDICAL": "pharmacy",
    }


def test_build_waypoint_names():
    """Waypoint names are service, target house, then docking station."""
    assert build_waypoint_names("GROCERY", "house_3") == [
        "supermarket",
        "house_3",
        "docking_station",
    ]
    assert build_waypoint_names("FIRE", "house_5") == [
        "firefighting_center",
        "house_5",
        "docking_station",
    ]


@pytest.mark.parametrize("mission_type", SERVICE_LOCATIONS)
@pytest.mark.parametrize("target_house", VALID_HOUSES)
def test_all_20_mission_combinations_are_valid(mission_type, target_house):
    """All 4 by 5 mission combinations produce three waypoint names."""
    waypoint_names = build_waypoint_names(mission_type, target_house)

    assert len(waypoint_names) == 3
    assert waypoint_names[0] == SERVICE_LOCATIONS[mission_type]
    assert waypoint_names[1] == target_house
    assert waypoint_names[2] == DOCKING_STATION


@pytest.mark.parametrize(
    ("mission_type", "target_house"),
    [
        ("grocery", "house_1"),
        ("GROCERY ", "house_1"),
        ("GROCERY", "House_1"),
        ("GROCERY", "house_99"),
    ],
)
def test_validation_rejects_non_exact_strings(mission_type, target_house):
    """Mission strings are case-sensitive and whitespace-sensitive."""
    with pytest.raises(MissionValidationError):
        validate_mission(mission_type, target_house)


def test_missing_required_landmarks():
    """Landmark validation reports exactly absent required names."""
    landmark_names = set(REQUIRED_LANDMARKS)
    landmark_names.remove("restaurant")
    landmark_names.remove("house_4")

    assert missing_required_landmarks(landmark_names) == {
        "restaurant",
        "house_4",
    }
