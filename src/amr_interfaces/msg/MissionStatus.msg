# Status: IDLE, RUNNING, SUCCEEDED, FAILED, REJECTED
string status

# Name of the waypoint currently being navigated to
# (supermarket / restaurant / firefighting_center / pharmacy / house_N / docking_station)
string current_waypoint

# Progress 0.0 to 1.0 (fraction of waypoints completed in this mission)
float32 progress

# Human-readable detail: e.g. "Arrived at supermarket" or "Landmark not in database"
string message
