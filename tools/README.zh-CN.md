# 开发工具

<p align="center"><a href="README.md">English</a> | 中文</p>

本地环境检查与能力查询工具。

Bazel 依赖交付见 [离线构建](../docs/development/offline-build.zh-CN.md)。
`prepare_bazel_offline.py` 在联网机器上显式准备依赖包；`bazel_offline.py`
校验依赖包后执行禁止仓库下载的 Bazel 构建。与环境清点工具不同，这两个工具
会执行构建工具并写入构建产物。
当前工具使用 Python 3.10+ 标准库，不依赖 SDK。

## 环境清点

```bash
python3 tools/check_environment.py --profile host
python3 tools/check_environment.py --profile container --robot-type foot_quadruped
```

工作站模式检查 PATH 上的 Bash、Git 和 Docker；Bazel 仅在容器模式要求，容器模式检查 Bash、Git 和 Bazel，不要求 Docker。
实际 Docker 可用性检查及进入容器的步骤见[容器指南](../docker/README.zh-CN.md)。
Python 版本按本地工具基线 3.10 检查，不检查 SDK 原生依赖或设备 Python ABI。
其他工具仅查找、不执行；预期 Bazel 版本读取自 `.bazelversion`，
不是对已安装二进制版本的观测。

输出为 JSON。退出码 0 表示清点完成，未发现必需工具缺失或设备类型发布阻塞；
1 表示这些本地要求需要处理；2 表示输入或仓库／索引数据错误。
参数解析错误写入 stderr。
`sdk_status` 单独报告：当前仓库始终为 `blocked_integration`，即使本地清点退出码为 0。

工具不调用 Docker、不安装包、不拉取镜像、不通过 SSH 连接，也不调用机器人 API，
并明确列出未测试部分。不传设备类型时保持未选择；未知类型报错，
规划类型不因共用硬件就继承软件支持。

## 能力查询

```bash
python3 tools/vbot_catalog.py --robot-type foot_quadruped --capability device.agent.content
```

详见[索引格式与查询决策](../catalog/README.zh-CN.md)。
退出码 0 表示查询成功，包括返回被阻塞能力的情况；2 表示查询或索引错误。
工具不执行索引条目。

两个工具均根据自身文件的实际位置定位参考仓库，可在其他应用目录通过绝对路径调用。
仅在明确选择另一份完整 VBOT Lab 仓库时使用 `--root`。

## 设备 shell 清点

独立脚本已具备时，在配置好的设备 `vbot` shell 中运行：

```bash
python3 tools/check_device_environment.py
```

此工具检查有效账户、公开 setup 文件可读性、指定环境变量和 `aorta`／`ros2`／`timeout` 命令查找，
并拒绝抢先匹配到其他位置的 Aorta 程序。不输出当前环境值或会话文件内容，不运行工具、编辑文件或联系接口。
退出码 0 表示 shell 检查通过；1 表示需要处理；2 表示参数无效。
它不能证明设备身份、ROS 类型加载、实际收数或持久化有效。
与上方依赖仓库的工具不同，它不需要索引或 SDK，也不接受 `--root`。
手动检查、传输范围、`.bashrc` 配置及单独执行的有时限在线检查见[设备配置](../docs/getting-started/device-environment.zh-CN.md)。

## 验证与后续工具

```bash
python3 tests/check_repository.py
python3 tests/test_agent_workspace.py
bazel test //tests:repository_layout_test //tests:agent_workspace_test
```

Schema 生成、用户程序部署和设备日志收集工具仍处于规划阶段。
任务流程见 [Skills](../skills/README.zh-CN.md)，证据边界见[测试说明](../tests/README.zh-CN.md)。
