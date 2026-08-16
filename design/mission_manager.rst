.. _design_mission_manager:

================
Mission Manager
================

``easyfleet_mission_manager`` is the client-side library a mission-control
process (a hand-written script today; eventually an LLM-driven Behavior
Tree, or a PDDL planner) uses to discover a fleet's capabilities and drive
them — without ever linking against any capability's own implementation.

.. contents:: On this page
   :local:
   :depth: 2

The core types
===============

``FleetSession``
   Everything talking to a fleet actually needs, regardless of what
   decides *when* to command which robot: the ROS node and
   background-spinning executor every ``RobotHandle`` rides on, one shared
   capability-discovery pass, the registry of added robots, and the
   automatic RViz status markers ``RobotHandle::run_capability()``
   publishes. Deliberately has **no notion of "how a mission decides what
   to do next"** — only "how to talk to the robots once something has
   decided" — which is what makes it the right thing for more than one
   controller flavor to build on (see :ref:`design_extending_controllers`
   below).

``RobotHandle``
   A remote robot's capabilities, as seen and commanded from a mission
   script — the client-side counterpart to ``easyfleet_core::Robot``,
   which *hosts* real capability nodes. A ``RobotHandle`` owns no nodes at
   all: it's a thin, non-blocking, observable proxy over whatever this
   robot announced on ``/capabilities``, refreshed by the ``FleetSession``
   it was added to.

``SimpleController``
   The plain, manual controller: a mission script decides everything by
   hand (which robot runs which capability, when); ``SimpleController``
   just owns a ``FleetSession`` by composition and forwards every call to
   it. There is no decision-making logic here at all — that's deliberate,
   see :ref:`design_extending_controllers`.

A minimal mission script
==========================

.. code-block:: cpp

   easyfleet::init(argc, argv);
   easyfleet::SimpleController controller;

   easyfleet::RobotHandle robot_1("robot_1");
   controller.add_robot(robot_1);
   controller.discover_capabilities();

   if (!robot_1.has_capability("navigation")) { /* ... */ }

   robot_1.run_capability<easyfleet_mission_manager::Navigation>(
     "navigation", easyfleet_mission_manager::make_navigation_goal("kitchen"));

   while (robot_1.is_capability_running("navigation")) {
     controller.spin_some();
   }

   if (robot_1.capability_state("navigation") == easyfleet::CapabilityState::SUCCEEDED) {
     /* ... */
   }

   controller.shutdown();

``run_capability<ActionT>()`` sends a goal and returns immediately — the
non-blocking counterpart to a raw action client call — and automatically
publishes a status marker above the robot in RViz, kept up to date until
the goal settles or is stopped, so a mission script never has to remember
to do that itself.

``CapabilityState``: richer than running/not-running
=======================================================

``RobotHandle::capability_state()`` reports one of ``IDLE``, ``RUNNING``,
``SUCCEEDED``, ``ABORTED``, ``CANCELED``, ``REJECTED``, ``TIMEOUT`` or
``UNREACHABLE`` — deliberately more than a boolean, since "not running"
alone can't tell a mission script "it finished, and here's what actually
happened" apart from "nothing is happening because it crashed". Every
terminal value mirrors ``easyfleet_core::CapabilityClient``'s own outcome
one to one:

- ``CANCELED`` is a *deliberate*, expected outcome — either
  ``stop_capability()`` was called explicitly, or ``run_capability()``'s
  own timeout elapsed. Not a failure.
- ``UNREACHABLE`` means no recent heartbeat was seen on
  ``/capabilities_status`` at all — the capability may not even know a
  goal was sent, unlike every other terminal value, which means the
  capability itself is alive and responded (with success or a specific
  kind of failure).

Discovery
=========

``FleetSession::discover_capabilities()`` listens on ``/capabilities`` and
``/capabilities_status`` for a fixed window (2.5 s by default) and fans the
result out to every added ``RobotHandle``. This is a good match for a
scripted mission that discovers once at startup and then runs a bounded
sequence against whatever it found.

.. note::
   Capability discovery today is a **snapshot, not a live view**: nothing
   currently re-runs it mid-mission, and a robot that appears or
   disappears after the discovery window closes won't be reflected until
   it's re-run. ``RobotHandle::is_alive()``, unlike the discovery snapshot
   itself, *is* continuously tracked for the whole mission from
   ``/capabilities_status`` heartbeats — so a capability dying mid-mission
   is observable even though the fleet's capability *list* isn't
   re-scanned automatically. Turning discovery itself into a live,
   continuously-updated registry is the natural next step here, and the
   main remaining gap between this architecture and a long-running,
   LLM-driven control loop.

.. _design_extending_controllers:

Extensibility: building other controllers on ``FleetSession``
================================================================

``SimpleController`` is the reference example of "a controller with zero
decision-making logic of its own" — which also makes it the template for
writing a *different* one. A controller with real decision-making (an
``LLMController`` that asks a model what to do next from inside its own
``spin_some()``-driven loop, or a ``PlanSys2Controller`` whose PDDL action
implementations reach into the fleet through ``robots()``/``find_robot()``)
is meant to **own a ``FleetSession`` by composition**, the same way
``SimpleController`` does, and add whatever domain-specific logic it needs
around it — not subclass ``SimpleController`` itself. This mirrors how the
rest of EasyFleet favors composition over runtime-polymorphic base classes
(``ActionServerBase``, ``Capability<T>``).

.. note::
   ``LLMController``/``PlanSys2Controller`` themselves are not implemented
   yet — ``FleetSession``/``RobotHandle``/``SimpleController`` are the
   foundation those (or your own controller) would be built on, not a
   finished LLM-orchestration feature.
