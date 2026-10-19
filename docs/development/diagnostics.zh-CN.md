# 分层诊断

<p align="center"><a href="diagnostics.md">English</a> | 中文</p>

每层独立、显式执行。工具清点不代表授权连接机器人、安装软件或进入下一层。
diagnose.py 输出精简 JSON 摘要，不输出完整环境、会话内容、主机地址或异常堆栈。
分享到 [Vbot 超能社区](https://forum.vbot.cn/)前先审阅，不会自动发帖。

## 先区分语言

diagnose.py 的 sdk 和 sample 层级使用 **Python SDK**，不是 C++ SDK。
缺少 Python wheel 不代表 C++ 环境失败；C++ 应用在设备上不需要 Python venv 或 Python SDK，
请使用下方 [C++ 路径](#cpp)。inventory 与 device 仅检查工具／shell，不导入任一 SDK。

| 层级 | 执行位置 | 能确认什么 |
| --- | --- | --- |
| inventory | 宿主机或 CI | Python／Bash／Git 是否存在，SDK／设备保持 not_verified |
| sdk | 开发容器，选定 Python venv | Python 包元数据、wheel 原生库及 ABI，不创建 Node |
| device | 选定设备 vbot shell | 账户、会话文件可读及环境，不访问接口 |
| sample | 安装 Python SDK 的设备 vbot shell | 单路状态／电池／系统的原始样本，不判断解码后的业务行为 |

## Python：本地检查

在宿主机或 CI 的仓库根目录执行：

```bash
python3 tools/diagnose.py --level inventory
```

开发容器内，使用已安装配套 Python SDK 的 venv：

```bash
.venv/bin/python tools/diagnose.py --level sdk
```

预期包检查及 native_runtime_abi 为 confirmed。confirmed_missing 表示缺少工具／包，
mismatch 表示版本不同。清点成功不代表 SDK 已安装，不自动安装缺失依赖。

## Python：设备检查

先登录选定设备，独立 diagnose.py 无需完整仓库；传入此文件与传入应用一样，是单独显式的步骤。
按[设备环境](../getting-started/device-environment.zh-CN.md)设置 PATH 和 ZENOH_SESSION_CONFIG_URI。
在设备 shell 中，从放置 diagnose.py 的目录执行：

```bash
python3 diagnose.py --level device --allow-device-check
```

Python SDK 采样使用应用 venv，将示例路径替换为 APP_DIR，先清除 ROS／Python 覆盖：

```bash
unset PYTHONPATH &&
unset AORTA_CORE_FFI_LIB &&
export PYTHONNOUSERSITE=1 &&
/userdata/vbot/apps/my-app-REPLACE/.venv/bin/python diagnose.py \
  --level sample --allow-device-check --route state --timeout 5
```

只接受 state、battery 和 system，不采集音视频、不发布、不调用 service／action、不扫描目录或执行 SSH。
缺少 --allow-device-check 时在检查设备前停止。
sample_received 仅表示字节到达；decoded:false 不代表业务语义验证，解码交给应用。
waiting_data_timeout 将接口支持与生产者状态保留为 not_verified，不判定 ACL／固件问题。
missing_or_unreadable 不区分文件不存在还是不可访问。

sampling 对象记录执行进度，不声称远端已连通：

| 字段 | 含义 |
| --- | --- |
| attempted | 设备前置检查通过后，已尝试 SDK 采样 |
| session_opened | 已成功进入本地 SDK Node 上下文 |
| subscription_created | 已成功进入选定路由的本地订阅上下文 |
| sample_received | 本诊断已收到原始数据 |

interfaces_contacted 保留兼容，true 仅表示 subscription_created，
不表示已联系到生产者或确认接口受支持；false 也不能证明未尝试任何网络活动。
SDK／会话／订阅失败会保留已完成阶段并标明失败环节，不分享原始异常内容。
收到数据后的清理失败仍会使本次检查失败。

退出码 0 表示所选层级通过，1 表示阻塞／需要处理，2 表示参数错误；采样时限为 (0, 30] 秒。
工具不确认应用版本、不重启服务或修改权限。

<a id="cpp"></a>
## C++：构建输入、部署运行库与采样

### SDK 输入——开发容器

按 [C++ SDK 指南](../../packages/aorta/cpp/README.zh-CN.md)设置已校验的
AORTA_CPP_SDK_DIR 和 AORTA_EDU_SCHEMA_DIR，然后检查：

```bash
test -n "$AORTA_CPP_SDK_DIR" &&
test -n "$AORTA_EDU_SCHEMA_DIR" &&
test -r "$AORTA_CPP_SDK_DIR/include/aorta/node.h" &&
test -r "$AORTA_CPP_SDK_DIR/lib/libaorta_cpp.a" &&
test -r "$AORTA_EDU_SCHEMA_DIR/include/locomotion_status_generated.h" &&
g++ -dumpmachine &&
aarch64-linux-gnu-g++ -dumpmachine &&
file "$AORTA_CPP_SDK_DIR/lib/libaorta_core.so.13"
```

默认 g++ 生成容器原生代码，aarch64-linux-gnu-g++ 应输出 aarch64-linux-gnu。
选定 SDK 的 ELF 应与编译目标一致。文件存在和架构正确不代表应用链接／运行兼容。
在生成的 C++ 项目中，按 README 使用原生 SDK 执行模型／SDK／CLI 测试，
再使用 ARM64 SDK 和 --config=arm64 交叉构建。
不在 AMD64 容器运行 ARM64 测试，不用 host ldd 检查 ARM64 产物，
也不通过安装 Python wheel 处理 C++ 错误。

### 动态库——设备 vbot shell

以 [C++ 健康监测](../../templates/cpp-app/README.zh-CN.md)为例，获准 SSH 登录后，
将 APP_DIR 替换为实际输出的部署目录：

```bash
APP_DIR=/userdata/vbot/apps/cpp-app-REPLACE_FROM_OUTPUT &&
test "$(id -un)" = vbot &&
cd "$APP_DIR" &&
sha256sum -c SHA256SUMS &&
uname -m &&
export LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" &&
LDD_OUTPUT=$(ldd ./bin/health-monitor) &&
printf '%s\n' "$LDD_OUTPUT" &&
[[ "$LDD_OUTPUT" != *"not found"* ]]
```

预期校验通过、架构为 aarch64、没有缺失依赖。Aorta 运行库应来自此应用的 lib 目录。
缺少 libaorta_core.so.13 时检查完整部署包与 LD_LIBRARY_PATH。
Exec format error、GLIBC_* 或 GLIBCXX_* 表示需要核对编译器／SDK／系统运行库；
重新打包，不替换设备系统库。
其他 C++ 应用使用其文档中的可执行文件路径和完整部署清单。

### 单路采样——设备 vbot shell

收到只读采样请求后，可使用设备 Aorta CLI，不需要 Python SDK：

```bash
export PATH="/opt/vita/aorta/bin:$PATH" &&
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5 &&
test -r "$ZENOH_SESSION_CONFIG_URI" &&
timeout 12s aorta --group default topic echo /locomotion/status --count 1
```

只采样选定状态路由。CLI 的解码样本确认该路由／会话，不代表 C++ 程序的解码器正确。
需要检查健康监测的三路行为时，进入其 APP_DIR，加载文档中的运行环境，
显式执行 ./bin/health-monitor --config config.json --execute --duration 10。
区分回调接收时间与之后的出队时间；SDK 丢包及应用队列溢出都应停止，不以不完整输入继续。

CLI 可用而程序失败时，检查动态库、Schema 配套及实际进程环境；两者都超时时，原因仍待确认，
不为强行收数修改权限、设备模式或服务。下一步见[症状索引](../troubleshooting/README.zh-CN.md)。
