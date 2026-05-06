"""Mission planner shell without Nav2 goal execution.

Status: UNVERIFIED ON JAZZY/HARMONIC.

This node validates Mission requests, resolves waypoint names through the
landmark database, and publishes MissionStatus feedback. It intentionally does
not create a Nav2 action client or send navigation goals.
"""

from __future__ import annotations

from pathlib import Path

import rclpy
from amr_interfaces.msg import Mission, MissionStatus
from amr_navigation.landmark_db import (
    Landmark,
    LandmarkDatabaseError,
    load_landmarks_yaml,
)
from rclpy.node import Node

from amr_mission.mission_logic import (
    MissionValidationError,
    build_waypoint_names,
)


DEFAULT_LANDMARKS_PATH = (
    Path.cwd() / "src" / "amr_navigation" / "config" / "landmarks.yaml"
)


class MissionPlannerNode(Node):
    """Dry-run mission planner that stops before Nav2 integration."""

    def __init__(self) -> None:
        """Create subscriptions, publishers, and load landmark data."""
        super().__init__("mission_planner")
        self.declare_parameter("landmarks_yaml", str(DEFAULT_LANDMARKS_PATH))
        self._status_pub = self.create_publisher(
            MissionStatus,
            "/mission_status",
            10,
        )
        self.create_subscription(
            Mission,
            "/mission_request",
            self._mission_callback,
            10,
        )
        self._landmarks = self._load_landmarks()
        self._busy = False
        self._publish_status(
            status="IDLE",
            current_waypoint="",
            progress=0.0,
            message=(
                "Mission planner shell ready; "
                "Nav2 execution disabled"
            ),
        )

    def _load_landmarks(self) -> dict[str, Landmark] | None:
        """Load landmarks from the configured YAML path."""
        path = self.get_parameter("landmarks_yaml").value
        try:
            landmarks = load_landmarks_yaml(path)
        except (OSError, LandmarkDatabaseError) as exc:
            self.get_logger().warning(f"Landmark database unavailable: {exc}")
            return None

        self.get_logger().info(
            f"Loaded {len(landmarks)} landmarks from {path}"
        )
        return landmarks

    def _mission_callback(self, msg: Mission) -> None:
        """Validate and dry-run one mission request."""
        if self._busy:
            self._publish_status(
                status="REJECTED",
                current_waypoint="",
                progress=0.0,
                message="Mission planner is busy",
            )
            return

        self._busy = True
        try:
            self._handle_mission(msg)
        finally:
            self._busy = False

    def _handle_mission(self, msg: Mission) -> None:
        """Resolve mission waypoints without sending Nav2 goals."""
        try:
            waypoint_names = build_waypoint_names(
                msg.mission_type,
                msg.target_house,
            )
        except MissionValidationError as exc:
            self._publish_status(
                status="REJECTED",
                current_waypoint="",
                progress=0.0,
                message=str(exc),
            )
            return

        if self._landmarks is None:
            self._publish_status(
                status="REJECTED",
                current_waypoint="",
                progress=0.0,
                message="Landmark database not loaded",
            )
            return

        try:
            resolved = [
                self._landmarks[waypoint_name]
                for waypoint_name in waypoint_names
            ]
        except KeyError as exc:
            self._publish_status(
                status="REJECTED",
                current_waypoint=str(exc.args[0]),
                progress=0.0,
                message=f"Landmark not in database: {exc.args[0]}",
            )
            return

        route_summary = " -> ".join(
            f"{landmark.name}({landmark.x:.2f}, {landmark.y:.2f})"
            for landmark in resolved
        )
        self._publish_status(
            status="REJECTED",
            current_waypoint="",
            progress=0.0,
            message=(
                "Dry-run mission resolved; Nav2 execution disabled; "
                "no goal sent: "
                f"{route_summary}"
            ),
        )

    def _publish_status(
        self,
        status: str,
        current_waypoint: str,
        progress: float,
        message: str,
    ) -> None:
        """Publish one MissionStatus message."""
        status_msg = MissionStatus()
        status_msg.status = status
        status_msg.current_waypoint = current_waypoint
        status_msg.progress = float(progress)
        status_msg.message = message
        self._status_pub.publish(status_msg)


def main(args: list[str] | None = None) -> None:
    """Run the mission planner shell."""
    rclpy.init(args=args)
    node = MissionPlannerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
