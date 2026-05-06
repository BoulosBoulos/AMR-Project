# Mission Logic

Status: UNVERIFIED ON JAZZY/HARMONIC

This document describes the portable mission-name logic implemented in
`amr_mission/amr_mission/mission_logic.py`. It does not claim ROS 2, Nav2,
Gazebo, TF, or full-stack integration has been verified.

## Locked Strings

Mission types must remain exactly:

```text
GROCERY
FOOD
FIRE
MEDICAL
```

Landmark names must remain exactly:

```text
pharmacy
firefighting_center
supermarket
restaurant
house_1
house_2
house_3
house_4
house_5
docking_station
```

These strings are case-sensitive and whitespace-sensitive. The code rejects
variants such as `grocery`, `GROCERY `, `House_1`, or `house_99`.

## Mission Mapping

The service location for each mission type is:

| Mission type | Service landmark |
|---|---|
| `GROCERY` | `supermarket` |
| `FOOD` | `restaurant` |
| `FIRE` | `firefighting_center` |
| `MEDICAL` | `pharmacy` |

The target house must be one of:

```text
house_1
house_2
house_3
house_4
house_5
```

## Waypoint Names

The project-level mission description is:

```text
dock -> service_location -> target_house -> dock
```

The implemented waypoint-name helper assumes the robot starts at the dock, so
it returns only the commanded waypoints:

```text
service_location -> target_house -> docking_station
```

Example:

```python
build_waypoint_names("GROCERY", "house_3")
```

returns:

```python
["supermarket", "house_3", "docking_station"]
```

## Later Integration

The mission planner should use this module before sending any goal to Nav2:

1. Validate `Mission.mission_type` and `Mission.target_house`.
2. Build waypoint names.
3. Look up each name in the landmark database.
4. Convert landmark coordinates into `PoseStamped` goals in the `map` frame.
5. Send the resulting sequence to Nav2.
6. Publish `MissionStatus` updates for accepted, rejected, running, succeeded,
   and failed missions.

Anthony should verify this on the official Ubuntu 24.04 / ROS 2 Jazzy /
Gazebo Harmonic environment after Phase 3 and Nav2 integration are working.
