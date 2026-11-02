# 应用模板

<p align="center"><a href="README.md">English</a> | 中文</p>

这些文件供应用生成工具使用，不是机器人接口或可独立运行的示例。
生成器将模板中的说明／构建文件，与可运行的[健康监测 Blueprint](../blueprints/health-monitor/README.zh-CN.md)
组合成新项目。业务源码仍在 Blueprint 中维护，参考应用的修正会用于后续新生成的项目。
生成的项目以此应用为起点，不是任意机器人行为的通用生成器。

在开发容器内，从 VBOT Lab 根目录执行，输出选择新的目录：

```bash
python3 tools/create_app.py --language python --name my-python-app --output /tmp/my-python-app
python3 tools/create_app.py --language cpp --name my-cpp-app --output /tmp/my-cpp-app
```

两条命令相互独立。省略 --language 时仍默认 Python，不覆盖已有输出目录。
名称由 1–48 个小写字母、数字或连字符组成，以字母开头，以字母或数字结尾。
例如 my-app 有效，my-app- 会在创建文件前被拒绝。
生成过程不下载／安装 SDK，不运行 Bazel、不部署，也不连接机器人；构建前阅读生成项目的 README。

| 模板 | 生成项目 |
| --- | --- |
| [Python](python-app/README.zh-CN.md) | Python 源码／测试、Bazel 入口、固定依赖与 APP.json，使用 package_app.py 打包 |
| [C++](cpp-app/README.zh-CN.md) | C++ 源码／测试、本地 SDK 规则、复制的共用辅助代码、ARM64 工具链、原生／ARM64 构建步骤与二进制部署 |

README 与 AGENTS 文档会复制到新项目，供该项目的用户和 Coding Agent 使用。
.template 文件生成项目中的构建／测试文件，不是设备运行输入。
C++ 工作区包含构建逻辑及源码依赖，但不包含 SDK 二进制或头文件；
通过环境变量引用源码树之外已校验的原生／ARM64 发布制品。

两种语言均将同一份 gitignore.template 复制为 .gitignore，忽略本地环境文件、设备会话配置、
凭据字典、私钥文件名及打包产物；保留 .env.example，便于提供已脱敏的配置示例。
凭据应保存在项目之外。忽略规则不进行秘密扫描，也不保护已被 Git 跟踪的文件。
