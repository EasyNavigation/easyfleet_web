.. _build_and_install:

=================
Build & Install
=================

This page explains how to build **EasyFleet** from source and set up your
development environment.

.. contents:: On this page
   :local:
   :depth: 2

Supported platforms
--------------------

EasyFleet currently targets:

- **ROS 2 rolling**, on a recent Ubuntu.

.. note::
   EasyFleet is at an earlier, research stage than `EasyNavigation
   <https://easynavigation.github.io/>`_: there are no APT or Pixi binary
   packages yet, and only the **rolling** distro is currently exercised in
   CI. Building from source, in a workspace that also builds
   EasyNavigation, is the only supported install method today.

Prerequisites
-------------

1. ROS 2 Rolling

   You can either use a system-wide ROS 2 Rolling install, or a self-contained
   `Pixi <https://pixi.sh>`_ environment (the approach this project's own
   development workspace uses — see the ``pixi.toml``/``pixi.lock`` at the
   root of the workspace for the exact dependency set).

   .. code-block:: bash

      # System-wide ROS 2:
      source /opt/ros/rolling/setup.bash

      # ...or a Pixi environment already set up for "rolling":
      eval "$(pixi shell-hook -e rolling --frozen)"

2. ROS dependencies

   .. code-block:: bash

      sudo rosdep init   # only once per machine
      rosdep update

3. A few extra system packages EasyFleet itself needs on top of a plain
   ROS 2 install: ``nlohmann-json3-dev`` (JSON parsing in the mission
   manager and the EasyNav deployment) and ``behaviortree_cpp`` (the
   Behavior-Tree-based navigation capability). Both are picked up
   automatically by ``rosdep`` below.

.. _build_from_source:

Build from source
-------------------

Workspace layout
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   mkdir -p ~/easyfleet_ws/src
   cd ~/easyfleet_ws

Clone sources
~~~~~~~~~~~~~

EasyFleet is built on top of `EasyNavigation
<https://easynavigation.github.io/>`_: a working EasyFleet workspace needs
both, plus EasyNav's own plugin collection and its (transitive) dependencies.

.. code-block:: bash

   cd ~/easyfleet_ws/src
   git clone -b rolling https://github.com/EasyNavigation/EasyFleet.git
   git clone -b rolling https://github.com/EasyNavigation/EasyNavigation.git
   git clone -b rolling https://github.com/EasyNavigation/NavMap.git
   git clone -b rolling https://github.com/EasyNavigation/easynav_plugins.git
   git clone -b rolling https://github.com/fmrico/yaets.git

For the examples used throughout :doc:`../getting_started/index` and
:doc:`../examples/index` (maps, parameter files, RViz configurations, and a
Gazebo simulation), also clone:

.. code-block:: bash

   cd ~/easyfleet_ws/src
   git clone https://github.com/EasyNavigation/easynav_indoor_testcase.git
   git clone -b rolling https://github.com/EasyNavigation/easynav_playground_kobuki.git
   # easynav_playground_kobuki's own third-party dependencies (robot description, sim assets):
   vcs import . < easynav_playground_kobuki/thirdparty.repos

Install dependencies
~~~~~~~~~~~~~~~~~~~~~

From the workspace root, resolve every package's dependencies with rosdep:

.. code-block:: bash

   cd ~/easyfleet_ws
   rosdep install --from-paths src --ignore-src -y -r

Configure and build
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/easyfleet_ws
   colcon build --symlink-install

Source the overlay
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Source ROS 2 first, unless you're already in a Pixi shell that provides it
   source /opt/ros/rolling/setup.bash
   # Then source the workspace
   source ~/easyfleet_ws/install/setup.bash

Run tests (optional)
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/easyfleet_ws
   colcon test --packages-select easyfleet_core easyfleet_interfaces \
     easyfleet_mission_manager easyfleet_navigation_manager \
     easyfleet_easynav_navigation
   colcon test-result --verbose

Each ROS-communication test binary in EasyFleet runs on its own
``ROS_DOMAIN_ID``, so the suite is safe to run even alongside interactively
launched nodes — see :doc:`../developer_guide/index` for details.

Troubleshooting
----------------

- **Missing rosdep keys**

  Run ``rosdep check --from-paths src --ignore-src`` to diagnose. If a
  dependency is truly missing on your platform, please open an issue.

- **CMake not finding ROS packages, or EasyNav headers**

  Make sure both ROS 2 itself and this workspace's own ``install/setup.bash``
  are sourced, in that order, before building or running any executable —
  EasyFleet packages depend directly on EasyNavigation packages built in the
  same workspace.

- **ABI / stale build issues**

  Remove the build, install, and log folders and rebuild:

  .. code-block:: bash

     cd ~/easyfleet_ws
     rm -rf build install log
     colcon build --symlink-install

Uninstall / clean
------------------

Since this is a self-contained workspace overlay, you can remove it safely:

.. code-block:: bash

   rm -rf ~/easyfleet_ws

Next steps
----------

- :doc:`../getting_started/index` — bring up a single robot end to end
- :doc:`../examples/index` — the full catalogue of example deployments
- :doc:`../developer_guide/index` — architecture and internals for contributors

.. toctree::
   :hidden:
