.. _getting_started:

================
Getting Started
================

This page walks you through your **first EasyFleet deployment**: a single
robot, ``robot_1``, carrying three *mocked* capabilities — navigation,
manipulation, perception — plus a small mission script that discovers and
calls them. No simulator, no real navigation stack, no GPU needed: this is
the fastest way to see the capability-discovery-and-call pattern that every
other EasyFleet deployment builds on.

If you have not yet built EasyFleet, complete the steps in
:doc:`../build_install/index` first.

.. contents:: On this page
   :local:
   :depth: 2

Overview
--------

We will run the ``alone`` example deployment, shipped in the
``easyfleet_fake_alone_deployment`` package:

- **Robot:** ``robot_1``, hosting all three capability types, each a mock
  implementation (no external dependency, no real robot needed).
- **Mission control:** ``alone_mission_node``, a small script that discovers
  ``robot_1``'s capabilities and drives them, first sequentially, then in
  parallel.

Launching the deployment
-------------------------

With your workspace built and sourced (see :doc:`../build_install/index`):

.. code-block:: bash

   source ~/easyfleet_ws/install/setup.bash
   ros2 launch easyfleet_fake_alone_deployment alone_launch.yaml

This single command starts **both** halves of the deployment: the robot
(``robot_node``, hosting ``robot_1``'s three capabilities) immediately, and
mission control (``alone_mission_node``) a few seconds later, once the robot
has finished activating and announced itself.

Watch the terminal: ``alone_mission_node`` will, in order, print what it is
doing as it happens:

1. **Discover** which of ``robot_1``'s capabilities are currently active,
   and print each one's full description (read from ``/capabilities``).
2. Run ``navigation``, ``manipulation`` and ``perception``
   **sequentially**, each for up to 10 seconds or until it finishes on its
   own (whichever comes first), printing live feedback as it goes.
3. Run all three **in parallel**, same 10-second rule, printing interleaved
   feedback from all of them.

Poking at the robot by hand
----------------------------

You don't need a mission script to talk to a capability — any ROS 2 action
client works, since every capability is just a plain, discoverable ROS 2
action. In another terminal (with the workspace sourced):

.. code-block:: bash

   # What's running, and what does it look like?
   ros2 action list -t
   ros2 lifecycle get /robot_1/navigation
   ros2 topic echo /capabilities --once
   ros2 topic echo /capabilities_status

   # Send a navigation goal
   ros2 action send_goal /robot_1/navigation easyfleet_interfaces/action/Navigation \
     "{target_pose: {header: {frame_id: 'map'}, pose: {position: {x: 1.0, y: 2.0, z: 0.0}}}}" \
     --feedback

   # Send a perception goal (only the 'gato' class is supported by the mock)
   ros2 action send_goal /robot_1/perception easyfleet_interfaces/action/Perception \
     "{object_classes: ['gato']}" --feedback

Perception (and any preempted/canceled goal) runs until stopped: press
Ctrl-C on the ``send_goal`` command, or call ``ros2 action cancel`` from
another terminal, to stop it early.

Watching the fleet with the TUI
---------------------------------

``easyfleet_tools`` ships a read-only Terminal User Interface for watching a
running fleet without hand-assembling ``ros2 topic echo``/``ros2 action
send_goal --feedback`` calls:

.. code-block:: bash

   ros2 run easyfleet_tools tui

Its **Mission** tab shows the whole fleet at a glance: a robot list colored
by IDLE/BUSY/INACTIVE, that robot's capabilities, and the selected
capability's live goal status, feedback and result. Every discovered robot
also gets its own tab (capabilities, JSON description, execution status,
and a colored log feed), plus a fleet-wide **Logs** tab. Press **q** to
exit.

Running just the robot
------------------------

To bring up the robot without mission control automatically following it —
e.g. to poke at it entirely by hand, as above — launch its per-robot file
instead:

.. code-block:: bash

   ros2 launch easyfleet_fake_alone_deployment robot_1_launch.yaml

You can then run ``ros2 run easyfleet_fake_alone_deployment alone_mission_node``
separately, whenever you want, once the robot is up.

Next steps
----------

You have successfully run your first EasyFleet deployment!

Continue exploring:

- :doc:`../examples/index` — the full catalogue of example deployments,
  including multi-robot fleets and real navigation with EasyNavigation.
- :doc:`../design/index` — how capabilities, the Mission Manager and the
  Navigation Manager fit together.
- :doc:`../developer_guide/index` — internal architecture, for contributors
  and integrators writing their own capability backend.

.. toctree::
   :hidden:
