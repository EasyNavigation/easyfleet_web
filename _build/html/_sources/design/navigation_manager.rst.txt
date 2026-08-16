.. _design_navigation_manager:

===================
Navigation Manager
===================

``easyfleet_navigation_manager`` is a third kind of process, alongside a
robot and mission control: **one process per fleet**, not per robot, that
gives every robot's own `EasyNavigation <https://easynavigation.github.io/>`_
instance a single, shared view of the map and the route graph, and watches
every robot's planned path to prevent them from colliding with each other.

.. contents:: On this page
   :local:
   :depth: 2

Why a fleet-wide process at all
=================================

Left alone, every robot's own EasyNav ``maps_manager_node`` loads its own
local copy of the map and the route graph from disk. That works for one
robot, but two robots sharing the same physical space need to agree on
*the same* map and *the same* routes — and an operator editing a route
should see that edit reflected on every robot, not just the one they
happen to be looking at. ``navigation_manager_node`` is the single process
that owns that shared state and every robot's own EasyNav instance points
at.

.. graphviz::

   digraph nm {
     rankdir=TB;
     node [shape=box, style=rounded, fontname="verdana"];
     "navigation_manager_node" -> "/global_map" [style=dashed];
     "navigation_manager_node" -> "/global_routes" [style=dashed];
     "navigation_manager_node" -> "/global_routes_markers\n(RViz visualization)" [style=dashed];
     "navigation_manager_node" -> "/tf_static\n(map -> <robot>/map)" [style=dashed];
     "/global_map" -> "robot_1 maps_manager_node\n(incoming_map)";
     "/global_routes" -> "robot_1 maps_manager_node\n(incoming_routes)";
     "/global_map" -> "robot_2 maps_manager_node\n(incoming_map)";
     "/global_routes" -> "robot_2 maps_manager_node\n(incoming_routes)";
     "navigation_manager_node" -> "robot_1 planned path" [label="watches", style=dotted];
     "navigation_manager_node" -> "robot_2 planned path" [label="watches", style=dotted];
     "navigation_manager_node" -> "robot_1 EasyNav\n(pause/resume)" [label="GoalManager\nprotocol"];
     "navigation_manager_node" -> "robot_2 EasyNav\n(pause/resume)";
   }

Fleet-wide map and routes
============================

At startup, ``navigation_manager_node`` loads a map (currently a costmap,
via a pluggable ``MapPublisherBase`` — more representations can be added as
new factory entries) and a route graph, and publishes them:

- ``/global_map`` (``nav_msgs/OccupancyGrid``), transient-local — a robot
  that starts after this node still receives the retained map.
- ``/global_routes`` (``easynav_routes_maps_manager/RoutesMap``),
  transient-local, re-published every time the route graph is edited (see
  below).

Each robot's own ``maps_manager_node`` picks this up by remapping its own
per-plugin ``incoming_map``/``incoming_routes`` topics **to** these two
global ones (see :doc:`../examples/index` for the exact remap direction —
it must point *from* the plugin's own topic name *to* ``/global_map``, the
reverse silently does nothing) — so every robot ends up with the exact
same map and routes, without each having to load or maintain its own copy.

Live-editable routes
=====================

The route graph is not just published once — it can be edited **live**,
directly in RViz, via the same interactive-marker mechanism EasyNav's own
``RoutesMapsManager`` plugin uses locally: each route segment shows a
toggle cube (red = view-only, green = edit mode); in edit mode, draggable
start/end markers with move/rotate controls, plus "add segment" and
"remove segment" buttons.

Every geometry-changing edit (dragging an endpoint, adding, or removing a
segment — not merely toggling edit mode) does two things automatically:

1. Re-publishes the updated route graph on ``/global_routes``, so every
   robot picks up the edit immediately.
2. Saves the change back to the same YAML file the routes were loaded
   from, so it survives a restart.

.. note::
   The plain visualization ``MarkerArray`` on ``/global_routes_markers``
   is kept alive by a low-rate periodic republish, not transient-local
   durability — a late-joining RViz session reliably receiving the
   *retained* sample of that specific message type turned out not to be
   guaranteed in this environment. The interactive markers themselves
   don't have this problem: they actively resend their full state to any
   newly connected client rather than relying on durability at all.

Tying the frames together
===========================

Every robot's own EasyNav instance applies its ``tf_prefix`` to its local
``map`` frame (e.g. robot 1's own frame is literally ``robot_1/map``),
while ``/global_map``/``/global_routes`` are both stamped with the plain,
unprefixed ``map`` frame. For the two to line up in one TF tree,
``navigation_manager_node`` also broadcasts one static, identity transform
``map`` → ``<robot_id>/map`` per watched robot, on ``/tf_static`` — every
robot in a fleet is assumed to share the exact same map, only their pose
*within* it differs, so identity is the correct transform.

Tracking which robots exist
==============================

The set of robots being watched (for the TF broadcast above, and for the
conflict monitor below) can be configured two ways:

- **``robots.static_list``** — a fixed list of robot namespaces. Simplest,
  and what every current example deployment uses.
- **Dynamic tracking** (when ``robots.static_list`` is empty) — a plain
  subscription to ``/capabilities_status`` records a heartbeat timestamp
  per robot; a periodic timer adds a watcher for any newly-heard-from
  robot and drops one whose heartbeat has gone stale for longer than
  ``robots.staleness_sec``. No extra ``rclcpp::Node``, executor, or thread
  is created for this — a deliberate constraint on this package: **one
  node, one executor**, everything driven by plain subscription callbacks
  and timers on that same node.

.. _design_conflict_detection:

Conflict detection and pause/resume
=======================================

``navigation_manager_node`` continuously watches every tracked robot's
currently planned path (one lightweight watcher per robot, all sharing the
same node) and, on a timer, checks every pair of robots for an imminent
path conflict:

- Two robots' *current positions* must be within
  ``conflict.proximity_radius_m`` of each other — a coarse, cheap
  pre-filter.
- Their lookahead path segments (the next ``conflict.lookahead_distance_m``
  of each robot's plan) must come within
  ``conflict.path_conflict_distance_m`` of each other at some point.

When both hold, the robot with the **longer remaining path** to its own
goal is paused — the one closer to finishing continues, clearing the
conflict zone sooner. Pausing/resuming is done over EasyNav's own
``GoalManager`` control protocol, the same mechanism a capability uses to
pause/resume a single robot's own navigation.

.. important::
   A robot that's **already paused** because of a conflict keeps yielding
   regardless of how the remaining-path-length comparison changes tick to
   tick — without this rule, a stationary robot's remaining path can
   become numerically shorter than the moving robot's, causing the two to
   flip which one yields back and forth. Once the conflict monitor decides
   who stops, that decision holds until the conflict genuinely clears.

Every conflict-check tick logs, at ``DEBUG`` level, why each nearby pair
either is or isn't considered a risk — including explicitly noting when
one side of a pair is already paused and yielding — so the monitor's
decisions are auditable live (``--ros-args --log-level
navigation_manager_node:=debug``). Pause/resume actions themselves are
logged at ``INFO``, visible by default.

Key parameters
==============

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Parameter
     - Meaning
   * - ``map_type``
     - Which ``MapPublisherBase`` implementation to use. Only
       ``"costmap"`` exists today.
   * - ``map.package`` / ``map.map_path_file``
     - Where to load the fleet-wide map from.
   * - ``routes.package`` / ``routes.map_path_file``
     - Where to load the fleet-wide route graph from (and where live edits
       are saved back to).
   * - ``routes.markers_republish_rate_hz``
     - How often the visualization ``MarkerArray`` is re-published (see
       the note above). Default 1 Hz.
   * - ``robots.static_list``
     - Fixed robot namespace list. Empty (the default) enables dynamic
       tracking instead.
   * - ``robots.staleness_sec`` / ``robots.rescan_rate_hz``
     - Dynamic-tracking-only: how long without a heartbeat before a robot
       is dropped, and how often that check runs.
   * - ``robots.planner_plugin_key``
     - The ``planner_types`` entry name each robot's ``PlannerNode`` is
       configured with — determines which per-robot path topic to watch.
   * - ``conflict.check_rate_hz``
     - How often the conflict-detection timer runs.
   * - ``conflict.lookahead_distance_m`` / ``conflict.path_conflict_distance_m`` / ``conflict.proximity_radius_m``
     - See :ref:`design_conflict_detection` above.
