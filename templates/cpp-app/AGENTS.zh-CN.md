# C++ 应用指令

<p align="center"><a href="AGENTS.md">English</a> | 中文</p>

先阅读 README.md 和 APP.json。业务状态放在 health_monitor/model.h，
FlatBuffer 访问放在 decoder.h，订阅和输出放在 main.cc。
构建、测试、预览及打包均在配套 VBOT 开发容器内执行，复用已有容器。
原生测试／预览使用原生 SDK，设备构建使用 ARM64 SDK 与 --config=arm64，
不在 AMD64 执行交叉产物。
工作区独立，不向源码 include、Bazel 标签或 local_repository 添加对 VBOT Lab 仓库的引用。
SDK 制品不加入源码版本控制。延后处理消息时先复制借用的数据，访问前验证 FlatBuffers。
默认运行是预览，测试不创建 Node 或连接设备。
设备运行须明确目标机器人、vbot shell、配套版本和 --execute。
只观察已说明的三路数据，新增控制或录制需单独的用户意图。
区分无数据与接口不支持，保留有界等待及资源释放。
增加运行文件／库时更新构建和打包清单，打包与部署分开。
保留用户文件和 Agent 配置，不为测试而配置自启动或修改 ACL。
