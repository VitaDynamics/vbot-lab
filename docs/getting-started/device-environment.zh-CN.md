# 设备 shell 环境

<p align="center"><a href="device-environment.md">English</a> | 中文</p>

在机器人上使用 Aorta 或 ROS 2 工具前，先配置 `vbot` 账户的 Bash 环境。
本指南适用于提供 `/opt/vita` 公开工具路径的当前 `foot_quadruped` EDU 软件。
请先核对[版本范围](../../release/compatibility.zh-CN.md)；机器狗共用连接说明不代表软件支持相同。

Aorta 是原生通信层。系统启动 `aorta_ros2_bridge`，兼容部分此前已公开的 ROS 2 接口。
这里只需加载客户端环境，不需要自行启动 bridge。
接口范围见[可用接口参考](../interfaces/aorta-ros2.zh-CN.md)。

## 1. 确认操作终端

按[有线连接指南](../robots/quadruped-common/connection.zh-CN.md)登录后，
在机器人的 SSH 终端执行以下命令，不是在工作站或开发容器中执行：

```bash
whoami
test -x /opt/vita/aorta/bin/aorta
test -r /opt/vita/aorta/edu/edu_session.json5
test -r /opt/vita/ros/humble/setup.bash
test -r /opt/vita/aorta/ros/local_setup.bash
```

预期身份为 `vbot`，每个 `test` 的退出状态均成功（成功时无输出）。
路径缺失或不可读时停止操作，核对已安装的软件版本与交付内容，必要时联系支持。
不要通过修改设备权限绕过问题。使用下列公开路径即可，无需其他环境初始化脚本。

## 2. 加载并持久化环境

先在当前 Bash shell 执行以下配置；任一 `source` 报错时停止。
先加载 ROS 基础环境，再加载 bridge 消息类型 overlay，最后设置 DDS 参数：

```bash
# BEGIN VBOT EDU environment
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5

source /opt/vita/ros/humble/setup.bash
source /opt/vita/aorta/ros/local_setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=178
export ROS_LOCALHOST_ONLY=1
# END VBOT EDU environment
```

需要持久化时，先把 `vbot` 账户已有的 `~/.bashrc` 备份到未使用的文件名，
再用文本编辑器添加一次上述配置块（文件不存在则创建）。已有 VBOT 配置块时就地更新，
保留其他设置，并检查后续是否有覆盖这些变量的内容。不要修改工作站的 `.bashrc`。

编辑后先检查语法，再加载：

```bash
bash -n ~/.bashrc && source ~/.bashrc
```

仅在语法检查成功后运行 `source`。加载 `.bashrc` 也会执行其中的其他命令，请先检查已有内容。
反复加载会把 Aorta 目录重复添加到 `PATH` 前部，不要循环追加或加载配置块。
重新打开一个 SSH 会话并重复下方检查，确认持久化有效。
如果交互式登录未读取 `.bashrc`，检查用户已有的登录启动文件，确保其加载 `.bashrc`，
不要直接替换整个启动文件。

| 设置 | 用途 |
| --- | --- |
| `PATH` | 查找设备上的 Aorta 命令行工具 |
| `ZENOH_SESSION_CONFIG_URI` | 选择随设备交付的 EDU Aorta 会话配置，不修改交付的文件（离机复制见 [SDK quickstart](../../packages/aorta/python/README.zh-CN.md)） |
| ROS 基础环境 + bridge overlay | 加载 ROS 2 Humble 工具及 bridge 的 ROS 消息／服务类型 |
| `RMW_IMPLEMENTATION` | 使用与 bridge 一致的 Fast DDS 中间件 |
| `ROS_DOMAIN_ID` | 选择 domain `178` |
| `ROS_LOCALHOST_ONLY` | 将 ROS 发现限制在设备本机 |

ROS 2 命令必须在设备上执行：此 bridge 的 DDS 传输仅限本机。
电脑设置相同 domain 并不能远程访问，仅修改 `ROS_LOCALHOST_ONLY` 也不会建立受支持的远程连接。
此 Aorta 会话文件同样用于设备端客户端，不是工作站客户端配置。

## 3. 不联系接口，先检查当前 shell

```bash
command -v aorta
command -v ros2
printf 'ZENOH_SESSION_CONFIG_URI=%s\n' "$ZENOH_SESSION_CONFIG_URI"
printf 'RMW_IMPLEMENTATION=%s\n' "$RMW_IMPLEMENTATION"
printf 'ROS_DOMAIN_ID=%s\n' "$ROS_DOMAIN_ID"
printf 'ROS_LOCALHOST_ONLY=%s\n' "$ROS_LOCALHOST_ONLY"
```

两个命令应能找到，变量值应与配置块一致。
需要机器可读结果时，在**同一个设备 shell** 中用 Python 3.10+ 运行
[check_device_environment.py](../../tools/check_device_environment.py)。设备上已有仓库时：

```bash
python3 tools/check_device_environment.py
```

从仓库根目录运行，或使用文件绝对路径。也可以按用户请求单独把此独立文件传到用户目录；
它不依赖 SDK 或仓库其他文件。不要给工作站检查器传入设备 profile。

JSON 报告检查有效账户、公开文件访问、命令查找与指定环境变量。
退出码 `0` 仅表示这些 shell 检查通过；`1` 表示需要处理；`2` 表示参数无效。
它不加载脚本、不读取会话配置内容、不编辑文件、不运行发现的工具、不建立网络连接，
也不检查在线接口。通过不代表 ROS overlay 类型能够加载、SDK 已安装或机器人功能可用。

## 4. 发现接口并接收一条数据

这是独立的只读设备操作，仅在任务包含设备检查时执行。
保持机器人静止，不要用发布控制消息或调用服务来测试环境。逐条执行并检查结果：

```bash
timeout 15s aorta topic list
timeout 15s aorta service list
timeout 15s aorta schema get /imu_raw
timeout 15s aorta topic echo /imu_raw --count 1
```

Aorta 列表可能包含标记为 `absent` 的目录条目。
路由可列出或 Schema 可查询，不代表有数据到达。最后一条命令应收到解码后的 IMU 数据；
超时应记录为观测窗口内未收数／结论不充分，不能标为成功。

```bash
timeout 15s ros2 topic list --no-daemon -t
timeout 15s ros2 service list --no-daemon -t
timeout 15s ros2 interface show sensor_msgs/msg/Imu
timeout 15s ros2 topic echo /imu_raw sensor_msgs/msg/Imu --no-daemon --once --qos-reliability best_effort
timeout 15s ros2 topic echo /servo/status --no-daemon --once --qos-reliability best_effort
```

`--no-daemon` 避免复用在其他环境下启动的 CLI daemon。IMU 检查标准 ROS 类型；
`/servo/status` 还会检查 overlay 中的 bridge 专用类型。
Humble 的 [echo 参数](https://github.com/ros2/ros2cli/blob/humble/ros2topic/ros2topic/verb/echo.py)
支持单条采样与 best-effort 订阅。`timeout` 确保没有活跃发布者时检查也会结束；
退出码 `124` 表示超时，不是通过。不要自动无限重试，也不要停止或重启系统服务。

分别报告环境、发现、Schema／类型加载和实际收数的结果。
不要用固定 topic 数量作为通过条件：辅助或派生 ROS topic、未活跃的发布者，以及不同版本的
接口集合都会影响列表。先检查单流，高带宽多流并发需要单独验证性能。

## 非交互命令与用户程序自启动

SSH 单条命令、Coding Agent 工具 shell 和自启动进程可能不读取交互式 `.bashrc`
（很多文件会在非交互模式提前返回）。子进程继承父进程已导出的环境；修改 `.bashrc`
不会更新已经运行的进程。在非交互 Bash 脚本中，应把同一配置块放在需要 Aorta／ROS 2
的命令前，加载失败则停止；不要假定 `bash -lc` 或 `source ~/.bashrc` 在所有启动配置下都有效。

通过 `/userdata/vbot/init.sh` 启动的用户程序也遵循这一规则：用 Bash 启动脚本先加载配置块，
再启动程序。若现有入口使用 `/bin/sh`，保留该入口，调用 Bash 启动脚本，
不要直接插入 Bash 的 `source` 语法。修改启动脚本是单独的用户请求，不属于检查器行为。
此环境配置既不改变账户权限，也不改变进程资源限额。

系统开机时以 vbot 身份调用此入口。完整的应用启动脚本、执行权限、后台启动、日志和停用流程，
见[用户程序自启动](../guides/user-autostart.zh-CN.md)。

## 故障排查

| 现象 | 下一步检查 |
| --- | --- |
| 找不到 `aorta` | 公开路径的二进制是否存在，当前 shell 的 `PATH` 是否含 `/opt/vita/aorta/bin` |
| 找不到 `ros2` | 两个 setup 文件是否可读、是否按顺序成功加载 |
| 只有 `/parameter_events` 与 `/rosout` | 是否设备本机终端、domain `178`、RMW、完整环境和 `--no-daemon`，然后核对版本支持 |
| ROS package／类型未知 | bridge overlay 加载情况与交付的消息类型；能发现 topic 不代表本地 typesupport 齐全 |
| Aorta Schema 查询超时 | 会话路径、交付配置是否可读、路由拼写与当前接口范围 |
| 能列出 topic，但 echo 超时 | 发布者活跃状态、类型加载、QoS 与接口文档中的使用条件；未收数不等于传感器故障 |
| 新 SSH 会话丢失环境 | 实际账户的 `.bashrc`、登录启动链及后续变量覆盖 |
| CLI 可用但应用／启动脚本失败 | 其父进程环境、Bash 加载、依赖及架构／ABI |

接口访问异常时，查阅[可用接口参考](../interfaces/aorta-ros2.zh-CN.md)，
提供软件版本、命令、退出状态和简短脱敏错误信息，不附带会话配置内容或访问令牌。
