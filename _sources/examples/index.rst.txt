.. _examples:

========
Examples
========

The example deployments live in their own repository,
`easyfleet_example_deployments <https://github.com/EasyNavigation/easyfleet_example_deployments>`_,
with its own CI: nine packages, each with its own launch files and config.
They range from fully mocked capabilities on a single robot to two robots
running real `EasyNavigation <https://easynavigation.github.io/>`_
navigation at once, isolated per robot over Zenoh or Fast DDS, and double
as integration tests for the whole architecture. See
:doc:`../build_install/index` for how to clone and build them.

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
       (mock); low-level API
     - ``launch/easynav_collaboration_launch.yaml``
   * - ``simple_api``
     - ``easyfleet_easynav_collaboration_simple_api_deployment``
     - ``robot_1``, ``robot_2``
     - same as ``easynav_collaboration``, with ``Deployment``/
       ``SimpleController``
     - ``launch/easynav_collaboration_launch.yaml``
   * - ``simple_api_py``
     - ``easyfleet_easynav_collaboration_simple_api_deployment_py``
     - ``robot_1``, ``robot_2``
     - same, with Python mock capabilities and a Python mission
     - ``launch/easynav_collaboration_launch.yaml``
   * - ``zenoh``
     - ``easyfleet_easynav_collaboration_zenoh_deployment``
     - ``robot_1``, ``robot_2``
     - same as ``simple_api``, one Zenoh island per robot
     - ``launch/easynav_collaboration_launch.yaml``
   * - ``fastdds``
     - ``easyfleet_easynav_collaboration_fastdds_deployment``
     - ``robot_1``, ``robot_2``
     - same as ``simple_api``, one ``ROS_DOMAIN_ID`` per robot
     - ``launch/easynav_collaboration_launch.yaml``
   * - ``farm``
     - ``easyfleet_easynav_farm_deployment``
     - ``robot_1`` (Summit XL)
     - navigation — real EasyNav on a NavMap, GPS localization
     - ``launch/robot_1_launch.yaml``

Every multi-robot scenario's top-level launch file starts **both** halves
of the deployment together: the robot(s) immediately, and mission control a
few seconds later, once the robot(s) have finished activating. Each robot
also has its own per-robot launch file that can be run standalone — see
:doc:`../design/index` for the robot/mission-control split this relies on.

.. note::
   The EasyNav scenarios need a real robot or a Gazebo simulation,
   **started separately**. The simulations now live in
   `easynav_playgrounds <https://github.com/EasyNavigation/easynav_playgrounds>`_
   (packages ``easynav_playground_kobuki``, ``easynav_playground_kobuki_worlds``,
   ...). The multi-robot examples' launch files still reference the archived
   ``easynav_playground_kobuki`` repository (its
   ``playgorund_multirobot_kobuki.launch.py``, and ``kobuki_description``/
   ``aws_robomaker_small_house_world`` in the Zenoh and Fast DDS
   ``simulation_launch.yaml``), and are being updated to
   ``easynav_playgrounds``. Its multi-robot simulation
   (``ros2 launch easynav_playground_kobuki_worlds multirobot_gazebo_sim.launch.yaml``)
   spawns the Kobukis as ``r1``/``r2`` with per-robot ``tf`` topics, not as
   ``robot_1``/``robot_2`` on a shared ``/tf`` as these examples expect.

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

   # in one terminal, if you don't have a real robot: Gazebo + one Kobuki,
   # unnamespaced, in the small house of the home2 map
   ros2 launch easynav_playground_kobuki_worlds gazebo_sim.launch.yaml

   # in another terminal:
   ros2 launch easyfleet_easynav_deployment easynav_gazebo_launch.yaml
   # or, namespaced to match a robot spawned under "robot_1":
   # ... robot_namespace:=robot_1

This launches the robot (EasyNav's ``system_main`` + the navigation
capability), an RViz window, ``navigation_manager_node`` (publishing the
map and routes on ``/global_map``/``/global_routes``) and, a few seconds
later, ``easynav_mission_node``, which sends the robot to one of three
configured waypoints and then demonstrates goal preemption: a second goal
sent while the first is still in flight redirects EasyNav without stopping
first, rather than queuing behind it.

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

Needs a two-robot Gazebo world, with the Kobukis spawned under
``robot_1``/``robot_2`` (see the note above), then:

.. code-block:: bash

   # both robots + navigation_manager_node + mission control
   ros2 launch easyfleet_easynav_collaboration_deployment easynav_collaboration_launch.yaml

This package is the **low-level** version: ``robot_node`` drives each
capability's lifecycle by hand, and the mission uses the free
``discover_capabilities()``/``run_capability()`` functions. See
``simple_api`` below for the same scenario with ``Deployment`` and
``RobotHandle``.

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

``simple_api``: the same scenario, simple API
================================================

Same robots, waypoints and five phases as ``easynav_collaboration``,
written against the simple API:

- ``robot_node`` is an ``easyfleet::Deployment`` that loads the mock
  capabilities listed in each robot's ``capabilities`` parameter as
  pluginlib ``CapabilityFactory`` plugins
  (``add_capabilities_from_parameters()``).
- The mission is a ``SimpleController`` with one ``RobotHandle`` per robot;
  ``run_capability()`` publishes the RViz status markers itself.

.. code-block:: bash

   ros2 launch easyfleet_easynav_collaboration_simple_api_deployment easynav_collaboration_launch.yaml

The top-level launch file also starts ``navigation_manager_node`` and an
RViz window showing the shared map and routes.

``simple_api_py``: the same scenario, in Python
==================================================

The Python mirror of ``simple_api``. Navigation is still the C++
EasyNav-backed capability, with ``simple_api``'s config and RViz files; the
mock perception and manipulation capabilities are Python
``Capability``/``ActionServerBase`` subclasses, each its own process run by
``spin_capability()``, and the mission is a Python ``SimpleController``/
``RobotHandle`` script (see :ref:`design_python_capability`):

.. code-block:: bash

   ros2 launch easyfleet_easynav_collaboration_simple_api_deployment_py easynav_collaboration_launch.yaml

``zenoh``: one Zenoh island per robot
=========================================

The ``simple_api`` scenario over ``rmw_zenoh_cpp``, isolating each robot as
it would be on its own computer: each robot's nodes connect only to that
robot's own Zenoh router, and each robot router connects to a central one
(where ``navigation_manager_node``, RViz and mission control run). The
robots never connect to each other. Each robot router's ACL
(``config/robot_N/zenoh_router.json5``) lets only the fleet-level contract
cross: ``/capabilities``, ``/capabilities_status``, ``/global_map``,
``/global_routes``, ``/clock``, the status markers, TF, and that robot's
capability actions, planned path, EasyNav control topic and robot
description.

``launch/simulation_launch.yaml`` starts the three routers, Gazebo, a
shared ``/clock`` bridge on the central island and both Kobukis, each in
its own island (see the note above about the simulation packages it
needs):

.. code-block:: bash

   # terminal 1: routers + Gazebo + both Kobukis
   ros2 launch easyfleet_easynav_collaboration_zenoh_deployment simulation_launch.yaml

   # terminal 2: both robots + navigation_manager_node + mission control
   ros2 launch easyfleet_easynav_collaboration_zenoh_deployment easynav_collaboration_launch.yaml

To inspect one island from a terminal, **source** (do not run) the
matching script first; it sets ``RMW_IMPLEMENTATION`` and
``ZENOH_SESSION_CONFIG_URI`` and stops the ROS 2 daemon:

.. code-block:: bash

   source $(ros2 pkg prefix easyfleet_easynav_collaboration_zenoh_deployment)/share/easyfleet_easynav_collaboration_zenoh_deployment/scripts/set_central.sh
   # or set_robot_1.sh / set_robot_2.sh
   ros2 topic list --no-daemon

``fastdds``: one ``ROS_DOMAIN_ID`` per robot
================================================

The ``simple_api`` scenario over the default Fast DDS, with a different
isolation strategy: the central island runs on ``ROS_DOMAIN_ID=0``,
``robot_1`` on ``1`` and ``robot_2`` on ``2``, and each robot's
`DDS Router <https://github.com/eProsima/DDS-Router>`_
(``config/robot_N/dds_router.yaml``) bridges its domain with the central
one, forwarding only the same fleet-level contract (an allowlist of
topics).

DDS Router is not a ROS package: build it once with
``scripts/build_dds_router.sh`` (default prefix
``~/.local/dds_router``, where the launch files look for the
``ddsrouter`` executable). Then, as with ``zenoh``:

.. code-block:: bash

   # terminal 1: Gazebo + both Kobukis, each in its robot's domain
   ros2 launch easyfleet_easynav_collaboration_fastdds_deployment simulation_launch.yaml

   # terminal 2: both robots (with their DDS Routers) + navigation_manager_node + mission control
   ros2 launch easyfleet_easynav_collaboration_fastdds_deployment easynav_collaboration_launch.yaml

``scripts/set_central.sh`` / ``set_robot_1.sh`` / ``set_robot_2.sh``
(sourced) set the matching ``ROS_DOMAIN_ID`` in a terminal.

``farm``: one Summit outdoors, NavMap + GPS
==============================================

One Summit XL, namespaced under ``robot_1``, running real EasyNav
navigation outdoors: a NavMap map with a routes layer on top, GPS
localization (``easynav_fusion_localizer``, fusing GPS, wheel odometry and
IMU) and no range sensor. It reuses ``easyfleet_easynav_deployment``'s
navigation capability and ships no mission script, only
``launch/robot_1_launch.yaml``:

.. code-block:: bash

   ros2 launch easyfleet_easynav_farm_deployment robot_1_launch.yaml

.. note::
   This scenario needs the ``granja_leon`` map/world package, which is not
   publicly available, and is therefore not in CI.

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
