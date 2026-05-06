"""Tests for portable landmark database validation."""

import pytest

from amr_navigation.landmark_db import (
    REQUIRED_LANDMARKS,
    LandmarkDatabaseError,
    get_landmark,
    parse_landmarks,
)


def _complete_landmark_data():
    return {
        "landmarks": {
            name: {"x": float(index), "y": float(-index)}
            for index, name in enumerate(sorted(REQUIRED_LANDMARKS))
        }
    }


def test_parse_complete_landmark_database():
    """All required landmarks are parsed with numeric coordinates."""
    landmarks = parse_landmarks(_complete_landmark_data())

    assert set(landmarks) == REQUIRED_LANDMARKS
    assert landmarks["pharmacy"].name == "pharmacy"
    assert isinstance(landmarks["pharmacy"].x, float)
    assert isinstance(landmarks["pharmacy"].y, float)


def test_missing_required_landmark_is_rejected():
    """A database missing any required landmark is not usable."""
    data = _complete_landmark_data()
    del data["landmarks"]["restaurant"]

    with pytest.raises(LandmarkDatabaseError, match="restaurant"):
        parse_landmarks(data)


@pytest.mark.parametrize(
    "bad_pose",
    [
        {"x": "0.0", "y": 1.0},
        {"x": 0.0},
        {"x": True, "y": 1.0},
        {"x": float("nan"), "y": 1.0},
        {"x": float("inf"), "y": 1.0},
        [0.0, 1.0],
    ],
)
def test_malformed_landmark_pose_is_rejected(bad_pose):
    """Landmark poses must be mappings with numeric x and y fields."""
    data = _complete_landmark_data()
    data["landmarks"]["pharmacy"] = bad_pose

    with pytest.raises(LandmarkDatabaseError):
        parse_landmarks(data)


def test_get_landmark_reports_unknown_names():
    """Lookup failures include the missing landmark name."""
    landmarks = parse_landmarks(_complete_landmark_data())

    with pytest.raises(LandmarkDatabaseError, match="house_99"):
        get_landmark(landmarks, "house_99")
