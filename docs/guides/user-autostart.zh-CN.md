# 用户程序开机自启动

<p align="center"><a href="user-autostart.md">English</a> | 中文</p>

系统启动时会**以 vbot 用户身份调用 `/userdata/vbot/init.sh`**。
通过此入口可在设备重启后自动拉起用户程序，无需先建立交互式 SSH 会话。
本指南适用于当前 `foot_quadruped` EDU 软件。

此脚本是开机入口，不是进程守护器：它本身不提供崩溃自动重启、日志轮转，
也不保证网络连接或机器人接口已就绪。应用需自行处理依赖未就绪的情况，设置有时限的等待并明确报错。
自启动不会增加账户权限，也不会改变进程资源限额。

## 1. 准备应用

先[连接设备并登录](../robots/quadruped-common/connection.zh-CN.md)，使用 vbot 账户。
以下命令在设备 SSH shell 中执行，不是在开发容器中执行：

```bash
whoami
test -w /userdata/vbot
command -v bash
command -v python3
command -v nohup
command -v flock
```

账户应为 `vbot`，各项检查均应成功；缺少命令时先解决依赖再继续。
将应用及匹配设备架构、Python 环境的依赖部署到设备。
下例使用你自己的前台 Python 程序 `/userdata/vbot/apps/my_app/main.py`，VBOT Lab 不提供此文件。
请按应用调整路径及解释器；使用虚拟环境时应指向其中的解释器。
部署注意事项见[开发流程](../development/README.zh-CN.md)。

```bash
umask 077
mkdir -p /userdata/vbot/apps/my_app/logs /userdata/vbot/apps/my_app/run
test -r /userdata/vbot/apps/my_app/main.py
```

应用文件缺失时停止。启用自启动前，确认应用启动行为安全且有明确的停止方法，
不要让设备开机无条件触发机器人运动。

## 2. 创建应用启动脚本

使用文本编辑器创建 `/userdata/vbot/apps/my_app/start.sh`，内容如下。
若文件已存在，修改前先备份到未占用的文件名：

```bash
#!/bin/bash
umask 077

export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
source /opt/vita/ros/humble/setup.bash || exit 1
source /opt/vita/aorta/ros/local_setup.bash || exit 1
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=178
export ROS_LOCALHOST_ONLY=1

cd /userdata/vbot/apps/my_app || exit 1
exec 9>/userdata/vbot/apps/my_app/run/my_app.lock || exit 1
if ! flock -n 9; then
    printf '%s\n' 'Cannot acquire my_app lock; check for an existing instance.' >&2
    exit 1
fi
exec python3 -u /userdata/vbot/apps/my_app/main.py
```

启动脚本显式加载[设备环境](../getting-started/device-environment.zh-CN.md)，
开机进程不能依赖交互式 `.bashrc` 的配置。
应用既不使用 Aorta 也不使用 ROS 2 时，可省略该环境块；仅使用 Aorta 时，
不需要 ROS 加载命令和 DDS 变量。

非阻塞文件锁用于避免通过同一启动脚本重复拉起应用。
应用应保持前台运行并保留文件描述符 `9`；`exec` 用应用替换启动脚本进程，
应用在整个运行期间持有该锁。不要通过删除锁文件强行启动第二个实例：文件存在不代表锁被占用。
绕过启动脚本直接运行应用，则不受此锁保护。

```bash
chmod u+x /userdata/vbot/apps/my_app/start.sh
bash -n /userdata/vbot/apps/my_app/start.sh
```

确认应用的操作前置条件后，先以前台方式运行一次，检查依赖和启动报错：

```bash
bash /userdata/vbot/apps/my_app/start.sh
```

按应用的停止方法退出（例如应用支持时使用 Ctrl+C），
确认它及其子进程均已退出后，再启用开机启动。此命令会实际运行应用，不是只读环境检查。

## 3. 配置开机入口

先检查 `/userdata/vbot/init.sh`。已有文件时，备份到未占用的文件名，
**保留现有解释器和其他启动命令**；仅添加一次下方标记块，放在任何无条件退出语句之前。
新建文件时，使用包含首行的完整示例：

```sh
#!/bin/sh
# BEGIN my_app autostart
nohup /bin/bash /userdata/vbot/apps/my_app/start.sh </dev/null >>/userdata/vbot/apps/my_app/logs/startup.log 2>&1 &
# END my_app autostart
```

末尾的后台运行符让开机入口及时返回；`nohup` 和重定向让应用不依赖终端输入，
并将输出保存在日志中。它们不提供崩溃恢复。
不要在开机入口中放交互式提示、前台无限循环或长时间的依赖等待。

对于上面新建的 POSIX shell 入口：

```bash
sh -n /userdata/vbot/init.sh && chmod u+x /userdata/vbot/init.sh
```

已有入口使用 Bash 时，改用 `bash -n` 检查并保留原解释器。
不要直接向 POSIX shell 入口插入 Bash 专用的环境命令，Bash 启动脚本已负责环境加载。
不要为测试单个应用而执行整个现有开机入口，否则可能同时拉起其他用户程序。

## 4. 确认重启后自启动

确认设备可以安全重启、当前没有其他任务后，按正常设备重启流程重启。
重新通过 SSH 登录，**先检查进程，不要手动启动应用**：

```bash
whoami
pgrep -a -u vbot -f '/userdata/vbot/apps/my_app/main[.]py'
ps -u vbot -o pid,ppid,lstart,args
tail -n 50 /userdata/vbot/apps/my_app/logs/startup.log
```

本例的常驻程序应只有一个实例，运行账户为 vbot；再结合应用自身的就绪信号确认启动完成。
开机入口返回成功，不表示后台应用已初始化成功。短时任务可能已经退出，
此时应检查应用自己的完成输出，而不是要求进程常驻。
应用不输出内容时日志可能为空；建议在应用日志中加入启动时间戳，以区分本次启动与历史记录。

## 5. 更新、停用与排障

- 停用此应用的自启动时，只删除或注释开机入口中属于它的标记块，保留其他应用的命令。
  这只影响后续启动，不会停止已经运行的进程。
- 停止当前实例时，使用应用自己的停止方法。手动发送终止信号前，先确认当前 PID、账户和命令，
  不要批量终止所有 Python 进程。应用及子进程退出后再替换文件或重新启动；更新前保留可恢复副本。
- 示例会向持久日志追加输出。根据应用配置有容量上限的日志或轮转，避免日志占满设备可写存储。
- 完全没有启动时，检查入口文件名、解释器、执行／读取权限、语法，以及应用、日志目录和运行目录是否存在。
  shell 脚本使用 Unix 换行符。
- 前台能运行、开机失败时，检查绝对路径、启动脚本环境和解释器，以及依赖在开机阶段是否可用。
  固定延时不能替代对依赖服务就绪状态的检查。
- 无法获取锁时，检查是否已有实例以及目录权限。应用退出时检查错误日志；此入口不会自动重启它。
