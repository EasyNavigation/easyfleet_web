.. _examples:

========
Examples
========

EasyFleet ships four self-contained example deployments, each its own
package under ``easyfleet_example_deployments/`` (own launch files, own
config). They range from fully mocked capabilities on a single robot to
two robots both running real `EasyNavigation <https://easynavigation.github.io/>`_
navigation at once — and double as integration tests for the whole
architecture.

If you haven't run any of these yet, :doc:`../getting_started/index`
walks through the simplest one (``alone``) step by step.

.. contents:: On this page
   :local:
   :depth: 2

Overview
========

.. list-table::
   :widths: 18 22 15 25 20
   :header-rows: 1

   * - Scenario
     - Package
     - Robot(s)
     - Capabilities
     - Launch file
   * - ``alone``
     - ``easyfleet_fake_alone_deployment``
     - ``robot_1``
     - navigation, manipulation, perception (mock)
     - ``launch/alone_launch.yaml``
   * - ``collaboration``
     - ``easyfleet_fake_collaboration_deployment``
     - ``robot_1``, ``robot_2``, ``robot_3``
     - navigation + perception (mock), navigation + manipulation (mock)
     - ``launch/collaboration_launch.yaml``
   * - ``easynav``
     - ``easyfleet_easynav_deployment``
     - one robot (namespace optional)
     - navigation — real EasyNav (costmap localizer/maps-manager/planner +
       regulated pure-pursuit controller)
     - ``launch/easynav_gazebo_launch.yaml``
   * - ``easynav_collaboration``
     - ``easyfleet_easynav_collaboration_deployment``
     - ``robot_1``, ``robot_2``
     - navigation (real EasyNav, both robots) + perception/manipulation
       (mock)
     - ``launch/easynav_collaboration_launch.yaml``

Every scenario's top-level launch file starts **both** halves of the
deployment together: the robot(s) immediately, and mission control a few
seconds later, once the robot(s) have finished activating. Each robot also
has its own per-robot launch file that can be run standalone — see
:doc:`../design/index` for the robot/mission-control split this relies on.

``alone``: one robot, three mocked capabilities
==================================================

The simplest deployment — no simulator, no real navigation stack. Covered
step by step in :doc:`../getting_started/index`.

.. code-block:: bash

   ros2 launch easyfleet_fake_alone_deployment alone_launch.yaml

``collaboration``: three robots, mocked capabilities
========================================================

``robot_1`` and ``robot_2`` (navigation + perception each), and ``robot_3``
(navigation + manipulation) — each hosted by its own process, discovered
and driven together by ``collaboration_mission_node``:

.. code-block:: bash

   ros2 launch easyfleet_fake_collaboration_deployment collaboration_launch.yaml

The mission runs two phases: first ``robot_1``/``robot_2`` run navigation
and perception together (all four goals at once, feedback labeled by each
capability's resolved action name so interleaved output stays legible);
then ``robot_3`` runs navigation to completion, followed by manipulation.

``easynav``: one robot, real navigation
==========================================

The ``navigation`` capability here is backed by a real EasyNav stack —
goals sent actually complete once the robot reaches the target waypoint,
not just after a fixed mock delay. Needs a real robot or a Gazebo
simulation of one, publishing scan/odometry/TF, **started separately**:

.. code-block:: bash

   # in one terminal, if you don't have a real robot:
   ros2 launch easynav_playground_kobuki playground_monorobot_kobuki.launch.py

   # in another terminal:
   ros2 launch easyfleet_easynav_deployment easynav_gazebo_launch.yaml
   # or, namespaced to match a Gazebo robot spawned under "robot_1":
   # ... robot_namespace:=robot_1

This launches the robot (EasyNav's ``system_main`` + the navigation
capability), an RViz window, and, a few seconds later,
``easynav_mission_node``, which sends the robot to one of three configured
waypoints and then demonstrates goal preemption: a second goal sent while
the first is still in flight redirects EasyNav without stopping first,
rather than queuing behind it.

RViz's own **2D Goal Pose** tool also works directly here — it publishes
to the same topic EasyNav's ``GoalManager`` subscribes to, so dragging a
goal in RViz drives the robot exactly like a scripted goal would.

``easynav_collaboration``: two robots, both real navigation
================================================================

Two robots, ``robot_1`` and ``robot_2``, both running real EasyNav
navigation at once on the same shared map — this is where
:doc:`../design/navigation_manager` actually matters: both robots point at
the same ``/global_map``/``/global_routes``, and the conflict monitor
watches both of their planned paths for imminent collisions. ``robot_1``
also carries a mock ``perception`` capability, ``robot_2`` a mock
``manipulation`` one.

Needs an actual two-robot Gazebo world:

.. code-block:: bash

   # terminal 1: spawns both Kobukis under /robot_1 and /robot_2
   ros2 launch easynav_playground_kobuki playgorund_multirobot_kobuki.launch.py

   # terminal 2: both robots + navigation_manager_node + mission control
   ros2 launch easyfleet_easynav_collaboration_deployment easynav_collaboration_launch.yaml

``easynav_collaboration_mission_node`` runs a longer, five-phase
choreography (simultaneous navigation to different waypoints, one robot
clearing space for the other, manipulation, and a mid-navigation redirect)
— every navigation goal is left to actually **succeed** rather than time
out quickly, so the mission takes a couple of minutes to run end to end.
At every phase transition, a floating status marker above each robot in
RViz shows what it's currently doing ("Navigating -> kitchen / Perceiving",
"Manipulating", ...) — published by
``easyfleet_mission_manager::StatusMarkerPublisher``, the same helper
``RobotHandle::run_capability()`` uses automatically (see
:doc:`../design/mission_manager`) — so watching RViz alone is enough to
follow the mission, no terminal needed.

Poking at a capability by hand
=================================

Every capability's action name is namespaced by robot. Against the
``alone`` scenario, for example:

.. code-block:: bash

   ros2 action list -t
   ros2 lifecycle get /robot_1/navigation
   ros2 topic echo /capabilities --once
   ros2 topic echo /capabilities_status

   ros2 action send_goal /robot_1/navigation easyfleet_interfaces/action/Navigation \
     "{target_pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 2.0, z: 0.0}}}}" \
     --feedback

Monitoring a running fleet
=============================

``easyfleet_tools`` provides a read-only TUI (``ros2 run easyfleet_tools
tui``) and a CLI (``ros2 easyfleet <verb>``) for watching any of the
scenarios above without hand-assembling ``ros2 topic echo``/``ros2 action
send_goal --feedback`` calls — see :doc:`../getting_started/index` for the
TUI, or run:

.. code-block:: bash

   ros2 easyfleet fleet                                   # every robot + capability, with status
   ros2 easyfleet describe robot_1/navigation              # full JSON description
   ros2 easyfleet watch robot_1/navigation --duration 10   # live goal status + feedback + result
   ros2 easyfleet status --duration 10                     # each robot's RViz status-marker text
   ros2 easyfleet logs --robot robot_1 --duration 10       # colored /rosout tail
