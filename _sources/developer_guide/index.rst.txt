.. _developer_guide:

================
Developer Info
================

This page is for anyone wanting to **contribute to EasyFleet**, or
**integrate their own robot/capability backend** on top of it — a
practical companion to :doc:`../design/index`, which covers the
architecture itself.

.. contents:: On this page
   :local:
   :depth: 2

API reference (Doxygen)
==========================

The full C++ API reference — every class, method, and parameter, generated
straight from the source — is published at:

  https://easynavigation.github.io/EasyFleet/

It's regenerated automatically on every push to the ``rolling`` branch (see
``.github/workflows/doxygen-doc.yml``), so it always reflects the latest
code, not just the last tagged release.

Repository layout
====================

EasyFleet is one monorepo, ``EasyNavigation/EasyFleet``, with one branch
per supported ROS 2 distro (``rolling`` today):

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Package
     - What it is
   * - ``easyfleet_core``
     - ``ActionServerBase``/``ActionClient``, ``Capability<ActionServerT>``/
       ``CapabilityClient``, ``Deployment``/``CapabilityFactory``, plus the
       ``Navigation``/``Manipulation``/``PerceptionActionServerBase`` domain
       base classes.
   * - ``easyfleet_interfaces``
     - ``CapabilityDescription``, ``CapabilityStatus``, and the
       ``Navigation``/``Manipulation``/``Perception`` actions.
   * - ``easyfleet_mission_manager``
     - ``FleetSession``, ``RobotHandle``, ``SimpleController``,
       ``CapabilityState`` — the client-side API described in
       :doc:`../design/mission_manager`.
   * - ``easyfleet_mission_manager_py``
     - The same API, a 1:1 Python port — for writing a mission controller
       in Python instead of C++.
   * - ``easyfleet_navigation_manager``
     - ``navigation_manager_node`` — see :doc:`../design/navigation_manager`.
   * - ``easyfleet_easynav_navigation``
     - The ``Navigate`` BT.CPP plugin node — the one resource EasyFleet
       itself provides for talking to EasyNav from a Behavior Tree.
   * - ``easyfleet_example_deployments/*``
     - The four example deployments — see :doc:`../examples/index`.
   * - ``easyfleet_tools``
     - The read-only fleet-monitoring TUI/CLI.

Building and testing
========================

See :doc:`../build_install/index` for the full setup. The short version,
once your workspace is built and sourced:

.. code-block:: bash

   colcon build --symlink-install --packages-select <package>
   colcon test --packages-select <package>
   colcon test-result --verbose

Every test binary that touches ROS communication runs on its own
``ROS_DOMAIN_ID`` (set explicitly in that package's ``test/CMakeLists.txt``,
via ``ament_add_gtest(... ENV ROS_DOMAIN_ID=NN)``), so the test suite stays
safe to run even alongside interactively launched nodes on the default
domain — they never cross-talk on shared topics like ``/capabilities``.

Every package also runs the standard ``ament_lint_auto`` suite
(``ament_cmake_copyright``, ``uncrustify``, ``cppcheck``, ``lint_cmake``,
``xmllint``) as part of ``colcon test`` — keep new code passing those
before opening a pull request.

Extending EasyFleet
=======================

Adding a capability backend
------------------------------

Subclass the matching ``easyfleet_core`` domain base class in your own
package — no changes needed to ``easyfleet_core`` or any example
deployment:

.. code-block:: cpp

   // my_nav2_capability/include/my_nav2_capability/navigation_nav2_capability.hpp
   class NavigationNav2ActionServer : public easyfleet_core::NavigationActionServerBase
   {
     // implement on_goal_received()/on_execute() by delegating to a real
     // nav2_msgs/action/NavigateToPose client internally
   };

Then make it loadable by ``easyfleet_core::Deployment`` with one
``PLUGINLIB_EXPORT_CLASS`` line — see
:ref:`the robot side, in Design <design>` for why ``Deployment`` loads a
``CapabilityFactory``, not the capability class itself:

.. code-block:: cpp

   PLUGINLIB_EXPORT_CLASS(
     (easyfleet_core::CapabilityFactoryFor<NavigationNav2ActionServer>),
     easyfleet_core::CapabilityFactory)

Two real reference implementations of this exact pattern exist in the
repo, at opposite ends of the "mock vs. real" spectrum: the fake
capabilities under ``easyfleet_fake_alone_deployment`` (a mock, simulates
progress on a timer, no external dependency), and
``easyfleet_easynav_deployment``'s real EasyNav-backed navigation
capability. Either is a good starting template.

Writing your own mission controller
--------------------------------------

Own a ``FleetSession`` by composition, the same way ``SimpleController``
does, and add whatever decision-making logic you need around it — in C++
(``easyfleet_mission_manager``) or Python (``easyfleet_mission_manager_py``),
your choice; both speak the same wire protocol, so they're interchangeable
against the same fleet. See :ref:`design_extending_controllers` in
:doc:`../design/mission_manager` for the pattern, and
:ref:`design_mission_manager` for a minimal example in both languages.
This, together with writing your own :doc:`deployment <../examples/index>`,
is where most integration work with EasyFleet actually happens.

Adding a fleet-wide map representation
------------------------------------------

``easyfleet_navigation_manager``'s ``map_type`` parameter selects a
``MapPublisherBase`` implementation from a small factory; only
``"costmap"`` exists today. Adding another representation is one new
``MapPublisherBase`` implementation registered in that factory, not a
rewrite of the rest of the node.

Known limitations
=====================

**Capability discovery is a one-shot snapshot, not a live view.**
``FleetSession::discover_capabilities()`` listens for a fixed window and
returns whatever it collected. That's good enough for a scripted mission
that discovers once at startup, but not for a long-lived, LLM-driven
Behavior Tree that needs to react to capabilities appearing or
disappearing mid-mission — see :doc:`../design/mission_manager` for what's
already tracked continuously (``RobotHandle::is_alive()``) versus what
isn't (the capability list itself). Turning discovery into a
continuously-updated, thread-safe registry — and deciding what should
happen to a goal already in flight when its capability's heartbeat stops
— is the single biggest gap between today's architecture and the
control-computer scenario it's meant to validate the plumbing for.

**``LLMController``/``PlanSys2Controller`` don't exist yet.**
``FleetSession``/``RobotHandle``/``SimpleController`` are the foundation
those would be built on — see :ref:`design_extending_controllers`.

Getting help / contributing
===============================

- 📦 Source code and issue tracker:
  `github.com/EasyNavigation/EasyFleet <https://github.com/EasyNavigation/EasyFleet>`_
- Found a bug, or want to propose a feature? Open an issue.
- Pull requests are welcome — please make sure ``colcon test`` (build +
  lint + unit tests) passes for any package you touch before opening one.
