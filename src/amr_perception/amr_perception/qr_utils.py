"""Portable QR detection and pose-estimation helpers.

Status: UNVERIFIED ON JAZZY/HARMONIC.

These helpers are intentionally independent of ROS 2, Gazebo, cv_bridge, and
TF. They operate on OpenCV images and camera calibration arrays only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


VALID_QR_PAYLOADS = frozenset(
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


@dataclass(frozen=True)
class QRDetection:
    """Decoded QR payload and its four image-space corner points."""

    payload: str
    corners: np.ndarray


def is_valid_landmark_payload(payload: str) -> bool:
    """Return True when a decoded QR payload is a locked landmark name."""
    return payload in VALID_QR_PAYLOADS


def detect_qr(frame: np.ndarray) -> QRDetection | None:
    """Detect and decode one QR code from an OpenCV image.

    Args:
        frame: OpenCV image, usually BGR or grayscale.

    Returns:
        A QRDetection when a non-empty payload and four corners are found;
        otherwise None.
    """
    if frame is None:
        raise ValueError("frame must not be None")

    detector = cv2.QRCodeDetector()
    payload, points, _ = detector.detectAndDecode(frame)

    if not payload or points is None:
        return None

    corners = _as_four_corners(points)
    return QRDetection(payload=payload, corners=corners)


def estimate_qr_pose(
    corners: Any,
    camera_matrix: Any,
    dist_coeffs: Any,
    qr_size: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate QR pose in the camera frame using ``cv2.solvePnP``.

    Corner order is assumed to match OpenCV QRCodeDetector output:
    top-left, top-right, bottom-right, bottom-left.

    Args:
        corners: Four image-space corner points with shape compatible with
            ``(4, 2)``.
        camera_matrix: 3 by 3 camera intrinsic matrix.
        dist_coeffs: OpenCV distortion coefficients.
        qr_size: Physical QR side length in meters.

    Returns:
        ``(rvec, tvec)`` from OpenCV, where ``tvec`` is the QR origin in the
        camera frame.

    Raises:
        ValueError: If inputs are malformed or pose estimation fails.
    """
    if qr_size <= 0.0:
        raise ValueError("qr_size must be positive")

    image_points = _as_four_corners(corners)
    camera_matrix = np.asarray(camera_matrix, dtype=np.float64)
    dist_coeffs = np.asarray(dist_coeffs, dtype=np.float64)

    if camera_matrix.shape != (3, 3):
        raise ValueError("camera_matrix must have shape (3, 3)")

    half_size = qr_size / 2.0
    object_points = np.array(
        [
            [-half_size, half_size, 0.0],
            [half_size, half_size, 0.0],
            [half_size, -half_size, 0.0],
            [-half_size, -half_size, 0.0],
        ],
        dtype=np.float64,
    )

    ok, rvec, tvec = cv2.solvePnP(
        object_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not ok:
        raise ValueError("cv2.solvePnP failed for QR corner inputs")

    return rvec, tvec


def rvec_tvec_to_matrix(rvec: Any, tvec: Any) -> np.ndarray:
    """Convert OpenCV pose vectors into a 4 by 4 homogeneous transform."""
    rvec = np.asarray(rvec, dtype=np.float64).reshape(3, 1)
    tvec = np.asarray(tvec, dtype=np.float64).reshape(3)
    rotation_matrix, _ = cv2.Rodrigues(rvec)

    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation_matrix
    transform[:3, 3] = tvec
    return transform


def draw_qr_detection(
    frame: np.ndarray,
    detection: QRDetection,
    color: tuple[int, int, int] = (0, 255, 0),
) -> np.ndarray:
    """Return a copy of the frame with QR corners and payload drawn on it."""
    if frame is None:
        raise ValueError("frame must not be None")

    output = frame.copy()
    corners = _as_four_corners(detection.corners)
    int_corners = np.round(corners).astype(np.int32)

    cv2.polylines(
        output,
        [int_corners],
        isClosed=True,
        color=color,
        thickness=2,
    )
    text_origin = tuple(int_corners[0])
    cv2.putText(
        output,
        detection.payload,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        1,
        cv2.LINE_AA,
    )
    return output


def _as_four_corners(points: Any) -> np.ndarray:
    """Return points as a validated float64 array with shape ``(4, 2)``."""
    corners = np.asarray(points, dtype=np.float64)
    if corners.shape == (1, 4, 2):
        corners = corners[0]

    if corners.shape != (4, 2):
        raise ValueError("QR corners must have shape (4, 2) or (1, 4, 2)")

    return corners
