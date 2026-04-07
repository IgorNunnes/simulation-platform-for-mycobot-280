# simulation-platform-for-mycobot-280

Repositorio do projeto com nome de publicacao. O nome interno do pacote ROS 2 permanece `mycobot_realsense_pick_sim`.

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
  ros-humble-image-view \
  ros-humble-joint-state-publisher-gui \
  ros-humble-tf2-geometry-msgs \
  ros-humble-xacro \
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

Pacotes externos da Elephant Robotics:

- `mycobot_description`
- `mycobot_280`

Esses dois pacotes nao vieram de `apt` neste host e nao possuem chave `rosdep` disponivel aqui. Eles precisam existir no mesmo workspace ROS 2, tipicamente clonados do repositorio da Elephant Robotics ou de um workspace que ja tenha esses pacotes.

Diagnostico validado nesta pasta:

- `ros2 launch mycobot_realsense_pick_sim sim_world.launch.py` falha porque `ros_gz_sim` nao esta instalado.
- `ros2 launch mycobot_realsense_pick_sim sim_bringup.launch.py` falha imediatamente porque o modulo Python `xacro` nao esta instalado.
- Mesmo apos instalar Gazebo/MoveIt, os launches `sim_bringup`, `topic_pose_control`, `pick_place` e `slider_control_sim` ainda exigem `mycobot_description`.
- O launch `slider_control_sim` tambem exige `mycobot_280` e `joint_state_publisher_gui`.

## Build

```bash
cd /home/igor/project_sim_cobot/simulation-platform-for-mycobot-280
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Se os pacotes da Elephant estiverem em outro workspace pai, faca o build a partir da raiz desse workspace e nao desta pasta isolada.

## Docker

Foi adicionado um ambiente Docker completo nesta pasta para evitar instalar toda a stack ROS 2, Gazebo, MoveIt e Elephant diretamente no host.

Arquivos:

- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `docker/entrypoint.sh`
- `run.sh`

O que a imagem faz:

- instala ROS 2 Humble Desktop
- instala `ros_gz`, `gz_ros2_control`, `moveit`, `xacro`, controllers e ferramentas de build
- baixa o repositorio oficial `elephantrobotics/mycobot_ros2` no branch `humble`
- compila `mycobot_description` e `mycobot_280` em `/opt/elephant_ws`
- monta esta pasta do projeto em `/workspaces/mycobot_realsense_pick_sim`

### Requisitos no host

- Docker Engine
- Docker Compose v2
- servidor grafico X11 ativo para abrir Gazebo e RViz

No host, permita acesso local ao X11 antes de rodar:

```bash
xhost +local:docker
```

### Fluxo de uso

Construir a imagem:

```bash
./run.sh build-image
```

Compilar este pacote dentro do container:

```bash
./run.sh build-ws
```

Abrir shell dentro do container:

```bash
./run.sh shell
```

Subir somente o mundo:

```bash
./run.sh sim-world
```

Subir Gazebo + robo + camera + bridges + controllers:

```bash
./run.sh sim-bringup rviz:=false
```

Subir controle por pose:

```bash
./run.sh topic-pose
```

Subir pick and place:

```bash
./run.sh pick-place
```

Subir modo slider:

```bash
./run.sh slider
```

### Observacoes importantes

- O `run.sh` usa teu `UID` e `GID`, entao os artefatos gerados em `build/` e `install/` continuam com permissao do teu usuario.
- Se o teu host usar Wayland puro, pode ser necessario iniciar uma sessao XWayland ou adaptar o compose para Wayland.
- Se o host nao tiver GPU configurada para containers, o Gazebo e o RViz ainda podem funcionar em renderizacao por software, mas mais lentos.
- Se depois tu quiser conectar camera real ou o braco real, sera preciso adicionar `devices:` ou regras USB ao `docker-compose.yml`.

### Subir no GitHub e publicar a imagem

Este repositorio ja pode ser versionado normalmente no GitHub sem levar junto artefatos locais de ROS 2, porque agora existe um `.gitignore` para `build/`, `install/`, `log/` e caches Python.

Tambem foi adicionado o workflow:

- `.github/workflows/docker-publish.yml`

Ele faz o seguinte:

- em `pull_request` para `main`: valida que o `docker/Dockerfile` builda
- em `push` para `main`: publica a imagem no GitHub Container Registry
- em tag `v*`: publica uma imagem versionada

Imagem publicada:

```bash
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:latest
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:main
ghcr.io/igornunnes/simulation-platform-for-mycobot-280:sha-<commit>
```

Se o repositorio estiver na tua conta `IgorNunnes`, o workflow vai publicar automaticamente nesse namespace. No GHCR o caminho costuma aparecer em minusculas.

Fluxo para subir:

```bash
git add .
git commit -m "Prepare repo and Docker publish workflow"
git push origin main
```

Depois do `push`, acompanhe em `GitHub > Actions`. Quando o workflow terminar, a imagem aparecera em `GitHub > Packages`.

Para testar a imagem publicada:

```bash
docker pull ghcr.io/igornunnes/simulation-platform-for-mycobot-280:latest
```

Se o pacote ficar privado por padrao no GHCR, altere a visibilidade em `GitHub > Packages > Package settings`.

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

- O host desta sessão nao tinha `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control`, `moveit`, `xacro` e os controladores `ros2_control` instalados, entao os launches falharam antes de fechar o ciclo completo.
- Os pacotes `mycobot_description` e `mycobot_280` nao estavam presentes neste workspace/host, entao o pacote nao consegue instanciar o robo nem o modo de slider sem esse codigo externo.
- A câmera foi montada fixa na célula, não no punho do braço.
- A detecção atual é por cor e não é robusta a mudanças fortes de iluminação.
- O attach/detach usa teleporte controlado, não contato físico real da garra.
