ARG ROS_DISTRO=humble
FROM osrf/ros:${ROS_DISTRO}-desktop

SHELL ["/bin/bash", "-lc"]

ARG ROS_DISTRO=humble
ARG ELEPHANT_REPO=https://github.com/elephantrobotics/mycobot_ros2.git
ARG ELEPHANT_BRANCH=humble
ARG DOCKER_USER=ros
ARG DOCKER_UID=1000
ARG DOCKER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=${ROS_DISTRO}
ENV ELEPHANT_WS=/opt/elephant_ws
ENV COLCON_HOME=/tmp/colcon

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    ca-certificates \
    curl \
    git \
    mesa-utils \
    python3-colcon-common-extensions \
    python3-opencv \
    python3-pip \
    python3-rosdep \
    python3-tk \
    python3-vcstool \
    ros-${ROS_DISTRO}-control-msgs \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-gazebo-msgs \
    ros-${ROS_DISTRO}-gz-ros2-control \
    ros-${ROS_DISTRO}-image-geometry \
    ros-${ROS_DISTRO}-image-view \
    ros-${ROS_DISTRO}-joint-state-broadcaster \
    ros-${ROS_DISTRO}-joint-state-publisher-gui \
    ros-${ROS_DISTRO}-joint-trajectory-controller \
    ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-ros2controlcli \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-tf2-geometry-msgs \
    ros-${ROS_DISTRO}-xacro \
    x11-apps \
 && rm -rf /var/lib/apt/lists/*

RUN rosdep init 2>/dev/null || true
RUN rosdep update || true

RUN if getent group "${DOCKER_GID}" >/dev/null; then \
      groupmod -n "${DOCKER_USER}" "$(getent group "${DOCKER_GID}" | cut -d: -f1)"; \
    else \
      groupadd --gid "${DOCKER_GID}" "${DOCKER_USER}"; \
    fi \
 && if getent passwd "${DOCKER_UID}" >/dev/null; then \
      usermod -l "${DOCKER_USER}" -d "/home/${DOCKER_USER}" -m "$(getent passwd "${DOCKER_UID}" | cut -d: -f1)"; \
    else \
      useradd --uid "${DOCKER_UID}" --gid "${DOCKER_GID}" -m -s /bin/bash "${DOCKER_USER}"; \
    fi \
 && mkdir -p /workspaces /tmp/colcon \
 && chown -R "${DOCKER_UID}:${DOCKER_GID}" /workspaces /tmp/colcon "/home/${DOCKER_USER}"

WORKDIR ${ELEPHANT_WS}/src
RUN git clone --branch "${ELEPHANT_BRANCH}" --depth 1 "${ELEPHANT_REPO}" mycobot_ros2

WORKDIR ${ELEPHANT_WS}
RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
 && colcon build --symlink-install --packages-select mycobot_description mycobot_280

COPY docker/entrypoint.sh /usr/local/bin/mycobot-entrypoint.sh
RUN chmod +x /usr/local/bin/mycobot-entrypoint.sh

ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1
ENV XAUTHORITY=/tmp/.Xauthority

WORKDIR /workspaces/mycobot_realsense_pick_sim
ENTRYPOINT ["/usr/local/bin/mycobot-entrypoint.sh"]
CMD ["bash"]
