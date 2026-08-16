.. _documentation_home:

*****
|LPN|
*****

.. raw:: html

    <h1 align="center">
      <div>
        <div style="position: relative; padding-bottom: 0%; overflow: hidden; max-width: 100%; height: auto;">
          <iframe width="675" height="380" src="https://www.youtube.com/embed/t3FxOrQwgKc?autoplay=1&mute=1" frameborder="1" allowfullscreen style="max-width: 100%;"></iframe>
        </div>
      </div>
    </h1>


Overview
########

**EasyFleet** is an open-source, ROS 2 framework for orchestrating **fleets of
multi-skill robots**, designed to be:

- ✅ **Capability-oriented**, not stack-specific: any robot skill — navigation,
  manipulation, perception, or a custom one — is exposed the same way, as a
  self-describing, lifecycle-managed ROS 2 action, regardless of which
  backend actually implements it.
- 🧩 **Backend-agnostic**, through a small set of base classes any
  integrator subclasses once: EasyFleet ships a real
  `EasyNavigation <https://easynavigation.github.io/>`_-backed navigation
  capability out of the box, but nothing in the architecture assumes EasyNav,
  Nav2, MoveIt, or any other specific stack.
- 🐝 **Fleet-aware from the ground up**: robots announce their own identity
  and capabilities at runtime from their ROS namespace, so a mission
  controller can discover, call, and monitor any number of robots without
  hardcoding who they are.
- 🗺️ **Centrally coordinated when it helps**: the Navigation Manager
  publishes one shared map and route graph for the whole fleet and watches
  every robot's planned path to prevent collisions between robots sharing
  the same space — without requiring every robot to re-implement that logic
  itself.
- 🚀 **Lightweight and simple to deploy**, using plain ROS 2 nodes, actions,
  and parameter files — no external orchestration framework required.

EasyFleet is developed by the `Intelligent Robotics Lab <https://intelligentroboticslab.gsyc.urjc.es/>`_
at Universidad Rey Juan Carlos, as the fleet-coordination layer that sits on
top of a per-robot navigation stack such as `EasyNavigation (EasyNav) <https://easynavigation.github.io/>`_.

It is structured around:

- **`easyfleet_core`**, a small C++ framework for building self-describing,
  lifecycle-managed ROS 2 actions ("capabilities") and their client-side
  counterparts.
- The **Mission Manager**, reusable building blocks for discovering active
  capabilities across a fleet and driving them from a mission script or a
  Behavior Tree.
- The **Navigation Manager**, a fleet-wide process that publishes a shared
  map and route graph, and continuously watches every robot's planned path
  to pause/resume robots on imminent conflicts.
- **Example deployments**, self-contained scenarios (mock capabilities,
  single- and multi-robot real EasyNav navigation) that double as
  integration tests for the whole architecture.

Whether you are prototyping a single robot with a handful of mocked
capabilities or coordinating several robots sharing the same navigable
space, EasyFleet provides the plumbing to discover, call, and monitor them
uniformly.

We invite you to explore, use, and contribute to this project!

📚 Learn more about the team behind the project in :ref:`about`.

📦 Source code: `github.com/EasyNavigation/EasyFleet <https://github.com/EasyNavigation/EasyFleet>`_

📢 Want to contribute? Feel free to open an issue, suggest a feature, or submit a pull request!

.. toctree::
   :hidden:

   build_install/index.rst
   getting_started/index.rst
   design/index.rst
   examples/index.rst
   developer_guide/index.rst
   about/index.rst
