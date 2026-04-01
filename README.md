# mycobot_realsense_pick_sim

Simulação isolada do braço `myCobot 280 M5` com câmera RGB-D estilo Intel RealSense no Gazebo Sim, percepção simples por visão e pipeline inicial de pick-and-place integrado ao MoveIt2.

## O que este pacote sobe

- Mundo SDF isolado para manipulação.
- Bancada branca com pedestal para o braço.
- `myCobot 280 M5` com garra adaptativa.
- Câmera RGB-D fixa observando a área de trabalho.
- Cinco blocos `4 cm x 4 cm x 4 cm`.
- Zona de coleta e zona de deposição.
- Bridge `ros_gz_bridge` para imagem RGB, depth, `camera_info`, `/clock` e `joint_states`.
- Nó de percepção com OpenCV.
- Nó de execução de pick-and-place com MoveIt2 + attach/detach por `SetEntityPose`.

## Dependências

Base ROS 2 / Gazebo / MoveIt:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-ros-gz \
  ros-humble-gz-ros2-control \
  ros-humble-moveit \
  ros-humble-cv-bridge \
  ros-humble-image-geometry \
  ros-humble-tf2-geometry-msgs \
  python3-opencv
```

Controladores ROS 2 necessários para a execução do braço em simulação:

```bash
sudo apt install -y \
  ros-humble-joint-state-broadcaster \
  ros-humble-joint-trajectory-controller \
  ros-humble-controller-manager \
  ros-humble-ros2controlcli
```

Observação:
No host usado nesta sessão, esses pacotes de controller não estavam instalados e o usuário não tinha `sudo` sem senha. Por isso o launch do Gazebo e da câmera foi validado, mas o ciclo completo de execução do braço ficou bloqueado na etapa de carga dos controladores.

## Build

```bash
cd /home/igor/limosim/limoatwork
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Launches

Somente o mundo:

```bash
ros2 launch mycobot_realsense_pick_sim sim_world.launch.py
```

Gazebo + braço + câmera + bridges + controllers:

```bash
ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py rviz:=false
```

Somente percepção:

```bash
ros2 launch mycobot_realsense_pick_sim vision.launch.py
```

Percepção + MoveIt2 + executor:

```bash
ros2 launch mycobot_realsense_pick_sim pick_place.launch.py
```

Tudo com um comando:

```bash
ros2 launch mycobot_realsense_pick_sim demo_full.launch.py
```

Controle manual tipo Elephant Robotics com sliders:

```bash
ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py
```

Controle manual por topico de pose:

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

## Tópicos principais

- `/camera/color/image_raw`
- `/camera/color/camera_info`
- `/camera/depth/image_rect_raw`
- `/camera/depth/camera_info`
- `/joint_states`
- `/detected_objects/poses`
- `/detected_objects/json`
- `/arm_goal_pose`

## Controle do braco por topico

O no `topic_pose_commander` assina `geometry_msgs/msg/PoseStamped` em `/arm_goal_pose` e usa IK + MoveIt2 para levar o end-effector ate a pose desejada.

Suba o ambiente:

```bash
ros2 launch mycobot_realsense_pick_sim topic_pose_control.launch.py
```

Depois publique uma pose de teste:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.18, y: 0.00, z: 0.62}, orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

Se quiser mandar uma pose sem orientar manualmente, envie a orientacao zerada e o no aplica uma orientacao padrao de grasp vertical:

```bash
ros2 topic pub --once /arm_goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.20, y: -0.08, z: 0.58}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 0.0}}}"
```

## Controle manual por slider

Para ter a mesma experiencia do `slider_control_adaptive_gripper` usado no braco real, foi criado um adaptador de simulacao baseado no pacote `mycobot_280`.

Use:

```bash
ros2 launch mycobot_realsense_pick_sim slider_control_sim.launch.py
```

Esse launch sobe:

- Gazebo + braco + camera
- RViz
- `joint_state_publisher_gui`
- `mycobot_280/slider_control_adaptive_gripper_sim`

Fluxo:

- o GUI publica em `/slider_joint_states`
- o no `slider_control_adaptive_gripper_sim` converte os sliders em trajetorias
- os controllers `/arm_controller/follow_joint_trajectory` e `/gripper_trajectory_controller/follow_joint_trajectory` movem o braco na simulacao

## TF esperada

- `world`
- `g_base`
- links do braço `joint1` a `joint6_flange`
- `gripper_base`
- `camera_link`
- `camera_color_optical_frame`
- `camera_depth_optical_frame`

## Validação rápida

Ver tópicos da câmera:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/color/image_raw
ros2 topic info /camera/depth/image_rect_raw
```

Ver detecção:

```bash
ros2 topic echo /detected_objects/json --once
```

Ver controladores:

```bash
ros2 control list_controller_types
ros2 param list /controller_manager
```

## Estratégia de percepção

- Segmentação HSV pragmática por cor.
- Contornos e filtro geométrico simples para quadrados.
- Profundidade no centróide para recuperar posição 3D.
- Transformação para `world` via `tf2`.

As bases e a mesa permanecem brancas, mas os blocos foram coloridos de forma proposital para garantir detecção robusta na primeira versão. Isso deixa o pipeline trocável depois para YOLO, segmentação ou detector clássico com textura/aresta em objetos brancos.

## Estratégia de manipulação

- MoveIt2 para IK e planejamento.
- Garra comandada por `FollowJointTrajectory`.
- Attach/detach simulado via `ros_gz_interfaces/srv/SetEntityPose`.

## Limitações conhecidas

- O host desta sessão não tinha os controladores `ros2_control` instalados, então a execução do pick-and-place não pôde ser fechada em runtime sem uma instalação `apt`.
- A câmera foi montada fixa na célula, não no punho do braço.
- A detecção atual é por cor e não é robusta a mudanças fortes de iluminação.
- O attach/detach usa teleporte controlado, não contato físico real da garra.
