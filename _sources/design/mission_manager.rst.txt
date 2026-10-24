.. _design_mission_manager:

================
Mission Manager
================

``easyfleet_mission_manager`` is the client-side library a mission-control
process (a hand-written script today; eventually an LLM-driven Behavior
Tree, or a PDDL planner) uses to discover a fleet's capabilities and drive
them — without ever linking against any capability's own implementation.

``easyfleet_mission_manager_py`` is a 1:1 Python port of the same three
types (``FleetSession``, ``RobotHandle``, ``SimpleController``), talking
the exact same wire protocol — everything on this page applies to both;
code samples are shown in both languages.

.. contents:: On this page
   :local:
   :depth: 2

The core types
===============

``FleetSession``
   Everything talking to a fleet actually needs, regardless of what
   decides *when* to command which robot: the ROS node and
   background-spinning executor every ``RobotHandle`` rides on, the live
   capability registry, the registry of added robots, and the
   automatic RViz status markers ``RobotHandle::run_capability()``
   publishes. Deliberately has **no notion of "how a mission decides what
   to do next"** — only "how to talk to the robots once something has
   decided" — which is what makes it the right thing for more than one
   controller flavor to build on (see :ref:`design_extending_controllers`
   below).

``RobotHandle``
   A remote robot's capabilities, as seen and commanded from a mission
   script — the client-side counterpart to ``easyfleet::Deployment``,
   which *hosts* real capability nodes. A ``RobotHandle`` owns no nodes at
   all: it's a thin, non-blocking, observable proxy over whatever this
   robot announces on ``/capabilities``, tracked live by the
   ``FleetSession`` it was added to. Adding it to a second session throws
   (``std::logic_error``, Python ``MissionManagerError``). In C++ it is not
   copyable, and destroying it detaches it from its session, dropping its
   running goals.

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

The same script in Python, against ``easyfleet_mission_manager_py``:

.. code-block:: python

   rclpy.init()
   controller = SimpleController()

   robot_1 = RobotHandle("robot_1")
   controller.add_robot(robot_1)
   controller.discover_capabilities()

   if not robot_1.has_capability("navigation"):
       ...

   robot_1.run_capability("navigation", Navigation, make_navigation_goal("kitchen"))

   while robot_1.is_capability_running("navigation"):
       controller.spin_some()

   if robot_1.capability_state("navigation") == CapabilityState.SUCCEEDED:
       ...

   controller.shutdown()

``run_capability()`` sends a goal and returns immediately — the
non-blocking counterpart to a raw action client call — and automatically
publishes a status marker above the robot in RViz, kept up to date until
the goal settles or is stopped, so a mission script never has to remember
to do that itself. The only real difference between the two languages:
C++'s ``run_capability<ActionT>()`` takes the action type as a template
parameter (fixing, at compile time, which ``ActionT`` a given
``capability_type`` means for the life of the handle); Python's
``run_capability()`` takes the same action module as a plain third
argument instead (``Navigation``, ``Manipulation``, ``Perception``, or one
of your own), checked at first use rather than at compile time.

``CapabilityState``: richer than running/not-running
=======================================================

``RobotHandle::capability_state()`` reports one of ``IDLE``, ``RUNNING``,
``SUCCEEDED``, ``ABORTED``, ``CANCELED``, ``REJECTED``, ``TIMEOUT`` or
``UNREACHABLE`` — deliberately more than a boolean, since "not running"
alone can't tell a mission script "it finished, and here's what actually
happened" apart from "nothing is happening because it crashed". Every
terminal value mirrors ``easyfleet_core::CapabilityClient``'s own outcome
one to one (Python ``CapabilityOutcome``):

- ``CANCELED`` is a *deliberate*, expected outcome — either
  ``stop_capability()`` was called explicitly, or ``run_capability()``'s
  own timeout elapsed, and the capability honored the cancel. Not a
  failure. The cancel is sent once.
- ``TIMEOUT`` means that cancel got no answer within about 5 s: the
  capability is alive but no longer answering for this goal.
- ``UNREACHABLE`` means the capability stopped sending heartbeats on
  ``/capabilities_status`` while its goal was running, or its action server
  could not be reached at all — the capability may not even know a goal
  was sent, unlike every other terminal value, which means the capability
  itself is alive and responded (with success or a specific kind of
  failure).

Discovery
=========

A ``FleetSession`` keeps a **live registry**: it subscribes to
``/capabilities`` (transient-local, so retained descriptions arrive late
too) and ``/capabilities_status`` for its whole life, so a capability that
appears, restarts or dies mid-mission is reflected in every
``RobotHandle`` without another discovery pass.
``FleetSession::discover_capabilities()`` (``window``, 2.5 s by default;
Python ``window_sec``) is just a **startup wait** that lets the registry
fill up before the mission's first decision.

These queries read the live registry:

- ``RobotHandle::has_capability()`` — the capability is announced and has a
  recent heartbeat.
- ``RobotHandle::is_alive()`` — a recent heartbeat was seen.
- ``RobotHandle::capabilities()`` — every capability this robot announced,
  returned by value.
- ``FleetSession::capabilities_of(robot)`` / ``FleetSession::is_alive(robot,
  capability)`` — the same, by robot name, for robots without a handle.

Python's ``FleetSession`` also has ``remove_robot()``. Only a description
that parses as a JSON **object** is considered valid.

Lower level: ``ActionClient``
------------------------------

``easyfleet_core::ActionClient<ActionT>`` (under ``CapabilityClient``) wraps
``rclcpp_action::Client``:

- ``cancel_all_goals()`` cancels only the goals **this client** sent,
  including ones the server has not accepted yet; other clients' goals on
  the same server are untouched.
- ``send_goal_and_wait()`` cancels the goal when its ``timeout`` elapses
  (``TIMEOUT``), and returns ``SERVER_UNAVAILABLE`` if the server
  disappears for longer than the client's server timeout.

.. _design_extending_controllers:

Extensibility: building other controllers on ``FleetSession``
================================================================

``SimpleController`` is the reference example of "a controller with zero
decision-making logic of its own" — which also makes it the template for
writing a *different* one. A controller with real decision-making (an
``LLMController`` that asks a model what to do next from inside its own
``spin_some()``-driven loop, or a ``PlanSys2Controller`` whose PDDL action
implementations reach into the fleet through ``robots()``/``find_robot()``)
is meant to own a ``FleetSession`` **by composition**, the same way
``SimpleController`` does, and add whatever domain-specific logic it needs
around it — not subclass ``SimpleController`` itself. This mirrors how the
rest of EasyFleet favors composition over runtime-polymorphic base classes
(``ActionServerBase``, ``Capability<T>``).

.. note::
   ``LLMController``/``PlanSys2Controller`` themselves are not implemented
   yet — ``FleetSession``/``RobotHandle``/``SimpleController`` are the
   foundation those (or your own controller) would be built on, not a
   finished LLM-orchestration feature.
