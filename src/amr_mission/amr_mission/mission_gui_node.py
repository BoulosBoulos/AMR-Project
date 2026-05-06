"""Tkinter mission GUI shell for the AMR final project.

Status: UNVERIFIED ON JAZZY/HARMONIC.

This node only publishes Mission requests and displays MissionStatus feedback.
It does not verify Nav2, Gazebo, bridge, TF, or full-stack integration.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import rclpy
from amr_interfaces.msg import Mission, MissionStatus
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

from amr_mission.mission_logic import (
    SERVICE_LOCATIONS,
    VALID_HOUSES,
    MissionValidationError,
    validate_mission,
)


WARNING_TEXT = (
    "UNVERIFIED ON JAZZY/HARMONIC. GUI shell only; "
    "does not verify Nav2, Gazebo, TF, or mission execution."
)


class MissionGuiNode(Node):
    """ROS 2 node backing the Tkinter mission GUI."""

    def __init__(self, app: "MissionGuiApp") -> None:
        """Create publishers and subscribers for mission GUI traffic."""
        super().__init__("mission_gui")
        self._app = app
        self._mission_pub = self.create_publisher(
            Mission,
            "/mission_request",
            10,
        )
        self.create_subscription(
            MissionStatus,
            "/mission_status",
            self._status_callback,
            10,
        )

    def publish_mission(self, mission_type: str, target_house: str) -> None:
        """Publish one mission request."""
        msg = Mission()
        msg.mission_type = mission_type
        msg.target_house = target_house
        self._mission_pub.publish(msg)
        self.get_logger().info(
            f"Published mission: {mission_type} -> {target_house}"
        )

    def _status_callback(self, msg: MissionStatus) -> None:
        """Forward mission status updates to the Tkinter main thread."""
        self._app.set_status_from_ros(msg)


class MissionGuiApp:
    """Small Tkinter app for submitting missions and viewing status."""

    def __init__(self) -> None:
        """Build the GUI widgets."""
        self.root = tk.Tk()
        self.root.title("AMR Mission Control")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._closed = False
        self.node: MissionGuiNode | None = None

        self.mission_type = tk.StringVar(value="GROCERY")
        self.target_house = tk.StringVar(value="house_1")
        self.status = tk.StringVar(value="IDLE")
        self.current_waypoint = tk.StringVar(value="")
        self.progress = tk.StringVar(value="0%")
        self.message = tk.StringVar(value="")

        self._build_widgets()

    def _build_widgets(self) -> None:
        """Create and place all Tk widgets."""
        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            main,
            text=WARNING_TEXT,
            foreground="#8a5a00",
            wraplength=320,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(main, text="Mission type").grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Combobox(
            main,
            textvariable=self.mission_type,
            values=sorted(SERVICE_LOCATIONS),
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="ew", pady=(0, 4))

        ttk.Label(main, text="Target house").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 4),
        )
        ttk.Combobox(
            main,
            textvariable=self.target_house,
            values=sorted(VALID_HOUSES),
            state="readonly",
            width=18,
        ).grid(row=2, column=1, sticky="ew", pady=(0, 4))

        ttk.Button(
            main,
            text="Submit Mission",
            command=self.submit_mission,
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 12))

        ttk.Label(main, text="Status").grid(row=4, column=0, sticky="w")
        ttk.Label(main, textvariable=self.status).grid(
            row=4,
            column=1,
            sticky="w",
        )

        ttk.Label(main, text="Waypoint").grid(row=5, column=0, sticky="w")
        ttk.Label(main, textvariable=self.current_waypoint).grid(
            row=5,
            column=1,
            sticky="w",
        )

        ttk.Label(main, text="Progress").grid(row=6, column=0, sticky="w")
        ttk.Label(main, textvariable=self.progress).grid(
            row=6,
            column=1,
            sticky="w",
        )

        ttk.Label(main, text="Message").grid(row=7, column=0, sticky="w")
        ttk.Label(main, textvariable=self.message, wraplength=260).grid(
            row=7,
            column=1,
            sticky="w",
        )

    def submit_mission(self) -> None:
        """Publish the mission selected in the GUI."""
        mission_type = self.mission_type.get()
        target_house = self.target_house.get()

        try:
            validate_mission(mission_type, target_house)
        except MissionValidationError as exc:
            self.message.set(str(exc))
            return

        if self.node is None:
            self.message.set("ROS node is not ready")
            return

        self.node.publish_mission(mission_type, target_house)

    def set_status_from_ros(self, msg: MissionStatus) -> None:
        """Schedule a GUI status update from a ROS callback thread."""
        if not self._closed:
            self.root.after(0, lambda: self._set_status(msg))

    def _set_status(self, msg: MissionStatus) -> None:
        """Apply a mission status message to Tk variables."""
        if self._closed:
            return

        self.status.set(msg.status)
        self.current_waypoint.set(msg.current_waypoint)
        self.progress.set(f"{msg.progress * 100.0:.0f}%")
        self.message.set(msg.message)

    def run(self) -> None:
        """Run the Tk main loop."""
        self.root.mainloop()

    def close(self) -> None:
        """Close the GUI window defensively."""
        self._closed = True
        self.root.quit()
        self.root.destroy()


def main(args: list[str] | None = None) -> None:
    """Run the mission GUI node."""
    rclpy.init(args=args)
    app = MissionGuiApp()
    node = MissionGuiNode(app)
    app.node = node
    executor = SingleThreadedExecutor()
    executor.add_node(node)

    spin_thread = threading.Thread(
        target=executor.spin,
        daemon=True,
    )
    spin_thread.start()

    try:
        app.run()
    finally:
        executor.shutdown()
        spin_thread.join(timeout=1.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
