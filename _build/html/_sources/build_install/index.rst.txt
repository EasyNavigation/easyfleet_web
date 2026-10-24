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

   .. code-block:: bash

      source /opt/ros/rolling/setup.bash

2. ROS dependencies

   .. code-block:: bash

      sudo rosdep init   # only once per machine
      rosdep update

3. A few extra system packages EasyFleet itself needs on top of a plain
   ROS 2 install: ``nlohmann-json-dev`` (JSON parsing in the mission
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
<https://easynavigation.github.io/>`_. The example deployments used
throughout :doc:`../getting_started/index` and :doc:`../examples/index` live
in their own repository,
`easyfleet_example_deployments <https://github.com/EasyNavigation/easyfleet_example_deployments>`_,
whose ``.repos`` file brings everything else:

.. code-block:: bash

   cd ~/easyfleet_ws/src
   git clone -b rolling https://github.com/EasyNavigation/easyfleet_example_deployments.git
   vcs import < easyfleet_example_deployments/easyfleet_example_deployments.repos

This clones, all on their ``rolling`` branch:

- `EasyFleet <https://github.com/EasyNavigation/EasyFleet>`__ itself.
- `EasyNavigation <https://github.com/EasyNavigation/EasyNavigation>`__,
  `easynav_plugins <https://github.com/EasyNavigation/easynav_plugins>`_,
  `NavMap <https://github.com/EasyNavigation/NavMap>`_ and
  `yaets <https://github.com/fmrico/yaets>`_: the EasyNav stack and its
  dependencies.
- `easynav_playgrounds <https://github.com/EasyNavigation/easynav_playgrounds>`_:
  Gazebo simulations (Kobuki, Summit XL, TIAGo, omnidirectional robots)
  with their worlds, maps and EasyNav configurations.
- `robot_localization <https://github.com/cra-ros-pkg/robot_localization>`_
  (``rolling-devel``), needed by ``easynav_fusion_localizer`` and not
  released as a binary for rolling.

Core only
^^^^^^^^^

To build just the EasyFleet packages, without the examples, clone EasyFleet
and its third-party dependencies (EasyNavigation, easynav_plugins, NavMap,
yaets). This is what EasyFleet's own CI builds:

.. code-block:: bash

   cd ~/easyfleet_ws/src
   git clone -b rolling https://github.com/EasyNavigation/EasyFleet.git
   vcs import < EasyFleet/.github/thirdparty_rolling.repos

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

   # Source ROS 2 first
   source /opt/ros/rolling/setup.bash
   # Then source the workspace
   source ~/easyfleet_ws/install/setup.bash

Run tests (optional)
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd ~/easyfleet_ws
   colcon test --parallel-workers 1 --packages-select \
     easyfleet_interfaces easyfleet_core easyfleet_mission_manager \
     easyfleet_mission_manager_py easyfleet_navigation_manager \
     easyfleet_easynav_navigation easyfleet_tools
   colcon test-result --verbose

``--parallel-workers 1`` runs one package at a time, as CI does. Each C++
ROS-communication test binary runs with
``ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`` and its own ``ROS_DOMAIN_ID``,
so it neither leaves the machine nor cross-talks with interactively launched
nodes. See :doc:`../developer_guide/index` for details.

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
