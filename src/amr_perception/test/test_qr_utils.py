"""Tests for portable QR helper functions."""

import numpy as np
import pytest

from amr_perception.qr_utils import (
    QRDetection,
    draw_qr_detection,
    estimate_qr_pose,
    is_valid_landmark_payload,
    rvec_tvec_to_matrix,
)


def test_payload_validation_uses_locked_landmark_names():
    """Payload validation accepts only exact landmark strings."""
    assert is_valid_landmark_payload("pharmacy")
    assert is_valid_landmark_payload("firefighting_center")
    assert is_valid_landmark_payload("docking_station")
    assert not is_valid_landmark_payload("Pharmacy")
    assert not is_valid_landmark_payload("pharmacy ")
    assert not is_valid_landmark_payload("house_99")


def test_estimate_qr_pose_front_parallel_square():
    """A centered QR square in the image estimates a forward camera pose."""
    camera_matrix = np.array(
        [
            [500.0, 0.0, 320.0],
            [0.0, 500.0, 240.0],
            [0.0, 0.0, 1.0],
        ]
    )
    dist_coeffs = np.zeros(5)
    corners = np.array(
        [
            [270.0, 190.0],
            [370.0, 190.0],
            [370.0, 290.0],
            [270.0, 290.0],
        ]
    )

    _rvec, tvec = estimate_qr_pose(
        corners,
        camera_matrix,
        dist_coeffs,
        qr_size=0.5,
    )

    assert tvec.shape == (3, 1)
    assert tvec[0, 0] == pytest.approx(0.0, abs=1.0e-6)
    assert tvec[1, 0] == pytest.approx(0.0, abs=1.0e-6)
    assert tvec[2, 0] == pytest.approx(2.5, abs=1.0e-6)


def test_estimate_qr_pose_accepts_opencv_detector_shape():
    """Detector output with shape (1, 4, 2) is accepted."""
    camera_matrix = np.eye(3)
    dist_coeffs = np.zeros(5)
    corners = np.array(
        [
            [
                [270.0, 190.0],
                [370.0, 190.0],
                [370.0, 290.0],
                [270.0, 290.0],
            ]
        ]
    )

    _rvec, tvec = estimate_qr_pose(corners, camera_matrix, dist_coeffs)

    assert tvec.shape == (3, 1)


def test_rvec_tvec_to_matrix_identity_rotation():
    """Pose vectors convert to a homogeneous transform."""
    transform = rvec_tvec_to_matrix(
        np.zeros((3, 1)),
        np.array([[1.0], [2.0], [3.0]]),
    )

    assert transform.shape == (4, 4)
    assert np.allclose(transform[:3, :3], np.eye(3))
    assert np.allclose(transform[:3, 3], [1.0, 2.0, 3.0])
    assert np.allclose(transform[3], [0.0, 0.0, 0.0, 1.0])


def test_draw_qr_detection_returns_modified_copy():
    """Debug drawing leaves the input frame untouched."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    detection = QRDetection(
        payload="pharmacy",
        corners=np.array(
            [
                [10.0, 10.0],
                [80.0, 10.0],
                [80.0, 80.0],
                [10.0, 80.0],
            ]
        ),
    )

    drawn = draw_qr_detection(frame, detection)

    assert drawn.shape == frame.shape
    assert np.count_nonzero(drawn) > 0
    assert np.count_nonzero(frame) == 0


@pytest.mark.parametrize(
    ("corners", "camera_matrix", "qr_size"),
    [
        (np.zeros((3, 2)), np.eye(3), 0.5),
        (np.zeros((4, 2)), np.zeros((2, 3)), 0.5),
        (np.zeros((4, 2)), np.eye(3), 0.0),
    ],
)
def test_estimate_qr_pose_rejects_malformed_inputs(
    corners,
    camera_matrix,
    qr_size,
):
    """Malformed geometry inputs are rejected before integration."""
    with pytest.raises(ValueError):
        estimate_qr_pose(
            corners,
            camera_matrix,
            np.zeros(5),
            qr_size=qr_size,
        )
