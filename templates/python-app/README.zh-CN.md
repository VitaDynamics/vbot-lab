# Python 应用工作区

<p align="center"><a href="README.md">English</a> | 中文</p>

这是基于只读健康监测应用的独立 Bazel 工作区。请在此修改应用，不必修改 VBOT Lab 参考仓库。
需要 Python 3.10+、Bazel 7.6.1 和 VBOT 开发容器。设备配套为 V1.6.0-12（foot_quadruped），
SDK Release edu-sdk-2026.10.14 提供固定版本依赖。

## 构建与测试——开发容器

在生成的应用根目录执行：

```bash
bazel build //:main &&
bazel test //:model_test &&
bazel run //:main &&
bazel run //:main -- --simulate
```

默认命令输出计划；模拟使用合成数据，不导入 SDK。
health_monitor/model.py 保存业务规则，runtime.py 管理设备订阅，main.py 管理参数、输出和退出。
编辑 config.json，或通过 `--config /path/to/config.json` 选择配置。
新鲜度使用回调中记录并随消息入队的单调时间，不是出队时间，也不比较不同数据流的时钟。
延后处理不会刷新旧样本；SDK 丢包及应用队列溢出都会停止程序。缺失或过期数据不等于硬件故障。
wire.py 使用配套 SDK 的 BFBS 元数据，在解码前校验三路消息结构。
坏包增加 invalid 而不刷新数据，合法的零值／默认字段仍有效。
校验限制为单包 1 MiB、64 层嵌套及 65,536 个对象，不验证生产者身份。
无需新增依赖；预览和模拟不加载这些 Schema。

Python 失败时在 stderr 输出 JSON，包含 status=error、stage、error_code 与 next_step，
不输出原始异常或配置内容。config_not_found、invalid_config 属于 stage=config，
在 SDK／设备访问前停止；sdk_not_installed、sdk_version_mismatch、sdk_load_failed 属于 stage=sdk。
环境与订阅失败使用各自阶段；未知错误使用 runtime/unexpected_error。
按 next_step 及[错误说明](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/troubleshooting/README.zh-CN.md#application-errors)处理。

## 打包——开发容器

使用配套 VBOT Lab 仓库和已准备 SDK 制品的绝对路径。
以下假设参考仓库位于 /workspace/vbot-lab，应用位于 /workspace/my-app：

```bash
python3 /workspace/vbot-lab/tools/package_app.py --project /workspace/my-app \
  --assets-dir /workspace/vbot-lab/artifacts/edu-sdk-2026.10.14 \
  --output /workspace/my-app-package &&
python3 /workspace/vbot-lab/tools/package_app.py --verify /workspace/my-app-package
```

替换为实际挂载位置。输出必须是应用目录之外的新目录。
APP.json 显式列出运行文件；增加模块或配置时同步更新。
仅打包列出的 Python／JSON 文件、LICENSE／NOTICE，以及四个固定 wheel 和校验清单。
不会复制 venv、会话配置或整个仓库。新增第三方依赖不会自动解析；
基础打包工具会拒绝与固定 SDK 配套不同的 requirements。
部署用 APP.json 由工具自动生成，不要将它加入 source_files。
顶层 APP.json、EDU_SDK_MANIFEST.json、SHA256SUMS、requirements.txt、application.tar.gz，
以及 wheelhouse/、licenses/ 的整个命名空间均为部署包保留路径。
打包和校验都会拒绝位于这些路径及其子路径中的应用文件。
自定义元数据可放在 app-info.json 或 health_monitor/ 内；health_monitor/APP.json 不会冲突。
传输前校验完整、尚未解压的包。解压只添加应用文件，不覆盖包文件，解压后原 SHA256SUMS 仍有效。

## 部署与运行——设备 vbot shell

先通过已有 SSH 连接，将完整的已校验包传入新的用户应用目录。
设备不需要仓库、编译器或 Bazel。登录后将 APP_DIR 改为实际目录：

```bash
APP_DIR=/userdata/vbot/apps/my-app-REPLACE &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
tar -xzf application.tar.gz &&
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
python3 -m venv .venv &&
.venv/bin/python -m pip install --no-index --find-links wheelhouse -r requirements.txt &&
.venv/bin/python -m pip check &&
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
.venv/bin/python -m health_monitor.main --config config.json --execute --duration 10
```

预期 JSON Lines 中各流状态为 waiting_data、receiving 或 stale。
只有三路均为新鲜数据时，最终 all_streams_receiving 才为 true。
实机运行只有在结束时三路数据都新鲜才以 0 退出；预览／模拟正常完成也以 0 退出。
退出码 1 表示结束时仍有数据缺失或过期，或配置／输入／运行失败，不一定是程序故障。
退出码 2 表示命令行参数错误，例如未知选项、无效时长或互斥模式冲突；Ctrl+C 以 130 退出。
low_battery 仅作提示，不触发任何控制；超时不能证明接口不支持。程序不会自动加入开机启动。
重新登录后，进入 APP_DIR、清除两个 Python 覆盖变量、设置相同环境，执行最后一条命令即可，无需重新安装。
退出时关闭订阅和 Node。

连接、环境和接口说明见 [VBOT Lab](https://github.com/VitaDynamics/vbot-lab)。
环境或无数据问题可按 [Python 诊断路径](https://github.com/VitaDynamics/vbot-lab/blob/main/docs/development/diagnostics.zh-CN.md)检查。
请在检查诊断摘要后，到 [Vbot 超能社区](https://forum.vbot.cn/)反馈可复现问题，不分享凭据或会话配置。
