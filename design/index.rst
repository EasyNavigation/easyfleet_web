.. _design:

======
Design
======

This section describes **EasyFleet's architecture**: how a robot's
capabilities are structured and hosted, how a mission-control process
discovers and drives them, and how the Navigation Manager coordinates
several robots sharing the same space.

.. contents:: On this page
   :local:
   :depth: 2

.. toctree::
   :maxdepth: 2
   :hidden:

   mission_manager.rst
   navigation_manager.rst

What's a "capability"?
=======================

A **capability** is the atomic unit EasyFleet builds everything around: one
``rclcpp_lifecycle::LifecycleNode`` (``easyfleet_core::Capability<ActionServerT>``)
wrapping exactly one ROS 2 action. Once activated, it:

- Publishes an ``easyfleet_interfaces/CapabilityDescription`` on the
  **reliable, transient-local** ``/capabilities`` topic — so anyone
  subscribing late still gets it. It carries ``robot``, ``capability`` and
  ``action_name`` (all resolved from the node's actual ROS namespace at
  runtime, not configured by hand) and a raw JSON description (what it
  does, its requirements, effects, parameters).
- Publishes a 1 Hz ``easyfleet_interfaces/CapabilityStatus`` heartbeat on
  ``/capabilities_status`` for as long as it stays active — how a mission
  controller knows a capability is not just registered but actually
  *alive*, and whether it currently has a goal executing (``busy``) or is
  free to be called, without sending it a goal just to find out.
- Exposes an ``allow_preemption`` parameter controlling whether a new goal
  can replace one that's currently running, or must be rejected until the
  current one finishes or is canceled.
- Can always be told to stop early — canceling the goal stops whatever the
  capability was doing: the robot stops moving, the perception stream
  stops reporting, the manipulator stops executing its trajectory.

Because a capability resolves its own identity from its ROS namespace,
the exact same binary announces itself correctly whether it's launched as
``/robot_1/navigation`` or ``/robot_2/navigation`` — nothing about a
capability's own code needs to know which robot it's running on.

.. graphviz::

   digraph capability {
     rankdir=LR;
     node [shape=box, style=rounded, fontname="verdana"];
     "Mission control\n(CapabilityClient)" -> "Capability<ActionServerT>\n(one ROS 2 action)" [label="goal"];
     "Capability<ActionServerT>\n(one ROS 2 action)" -> "Mission control\n(CapabilityClient)" [label="feedback / result"];
     "Capability<ActionServerT>\n(one ROS 2 action)" -> "/capabilities\n(transient-local)" [style=dashed];
     "Capability<ActionServerT>\n(one ROS 2 action)" -> "/capabilities_status\n(1 Hz heartbeat)" [style=dashed];
   }

Any integrator adds a new backend for a capability domain by subclassing
one of ``easyfleet_core``'s three domain base classes
(``NavigationActionServerBase``, ``ManipulationActionServerBase``,
``PerceptionActionServerBase``) and implementing ``on_goal_received()``/
``on_execute()`` — everything else (announcing itself, the heartbeat,
preemption bookkeeping, cancellation) is handled by ``Capability<T>`` and
needs no changes. EasyFleet ships one real backend this way, on top of
`EasyNavigation <https://easynavigation.github.io/>`_'s navigation stack
— see :doc:`../examples/index`.

Interfaces
==========

``easyfleet_interfaces`` defines three actions general enough that any
robot's implementation of a capability — any navigation stack, any
manipulator, any perception modality — can express itself through the same
interface, with a ``parameters_json`` escape hatch for stack-specific
tuning:

- **Navigation**: go to ``target_pose``, optionally via ordered
  ``waypoints``.
- **Manipulation**: reach a ``joint_target``, a ``pose_target``, or run a
  ``named_task``, selected by ``mode``.
- **Perception**: detect/report ``object_classes``, once or
  ``continuous``\ ly.

All three share a result-code convention (``SUCCESS=0``, ``REJECTED=1``,
``ABORTED=2``, ``CANCELED=3``, ``TIMEOUT=4``, with capability-specific
codes starting at ``10``) — documented, not enforced by the type system,
since ``.action`` files can't share constants across packages.

The robot side: ``Deployment`` and ``CapabilityFactory``
==========================================================

One process per robot, one ``easyfleet_core::Deployment`` per process —
matching reality: a real fleet's robots each have their own onboard
computer, so a deployment abstraction spanning several robots in one
process would be modeling something that doesn't exist outside a
single-machine simulation.

``Deployment`` replaces the configure → check → activate → check → spin →
deactivate → cleanup → shutdown dance every robot process would otherwise
repeat by hand, plus the "which concrete class does the string
``'navigation'`` mean" lookup: ``add_capability(name)`` loads a
pluginlib-registered ``CapabilityFactory`` for that name and constructs the
matching capability. A concrete backend becomes pluginlib-loadable with one
``PLUGINLIB_EXPORT_CLASS`` line, no boilerplate factory class of its own to
write (``CapabilityFactoryFor<YourActionServerT>`` covers every case). The
robot's identity comes entirely from the ROS namespace the process itself
was launched under — ``Deployment`` needs no namespace of its own.

.. code-block:: cpp

   easyfleet::init(argc, argv);

   easyfleet::Deployment deployment;
   deployment.add_capabilities_from_parameters("my_deployment_package");

   deployment.start();
   deployment.run();
   deployment.shutdown();

The mission-control side
==========================

A separate process discovers a fleet's capabilities and drives them —
never linked against any capability's implementation, only against
``easyfleet_interfaces``' action types. See :doc:`mission_manager` for
``FleetSession``/``RobotHandle``/``SimpleController``, the client-side API
built for this.

Robot vs. mission control
==========================

Every EasyFleet deployment is split into two kinds of process that never
link against each other's implementation, only ever talk over ROS
actions/topics:

.. graphviz::

   digraph split {
     rankdir=LR;
     node [shape=box, style=rounded, fontname="verdana"];
     subgraph cluster_robot1 {
       label="robot_1 process";
       style=dashed;
       "Deployment (robot_1)" -> "navigation" -> "perception";
     }
     subgraph cluster_robot2 {
       label="robot_2 process";
       style=dashed;
       "Deployment (robot_2)" -> "navigation (robot_2)" -> "manipulation";
     }
     "Mission control\n(FleetSession)" -> "navigation" [label="/capabilities,\n/capabilities_status,\nactions"];
     "Mission control\n(FleetSession)" -> "navigation (robot_2)";
     "Navigation Manager" -> "navigation" [label="/global_map,\n/global_routes,\npause/resume"];
     "Navigation Manager" -> "navigation (robot_2)";
   }

This split is what makes discovery meaningful in the first place: a
mission-control process has no compile-time knowledge of what robots exist
or which capabilities they carry — it finds out by listening on
``/capabilities``/``/capabilities_status``, the same way any other
operator or control-computer program would.
