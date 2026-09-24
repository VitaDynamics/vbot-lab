# 设备端 Skill 与 AGENTS.md 内容 API

<p align="center"><a href="content-api.md">English</a> | 中文</p>

通过这些 HTTP API，将开发者编写的内容注入设备上的 `vbot-agent-harness`。
这不是仓库 `skills/` 中 Coding Agent Skill 的安装方式。
请先阅读[适用范围与兼容性](README.zh-CN.md)及[编写示例](customization.zh-CN.md)。

## 连接与前提

约定服务基址为 `http://192.168.127.10:8787`，在设备开发环境中使用 `vbot` 账户访问。
服务随 EDU 镜像交付，写入前须确认交付版本支持这些路由。
不需要编译 Harness 源码、直接访问服务文件或修改权限。

这是 HTTP JSON，不是 MCP：不发送 JSON-RPC 包装、initialize 请求或 `Mcp-Session-Id`。
`18080` 端口的 MCP 工具服务是另一个访问目标。
仅在可信机器人网络中的单可信开发者场景使用服务。
不得将 `8787` 暴露或转发到不可信网络、校园公网或互联网。
指令不是操作系统权限或安全策略机制。

写请求使用 UTF-8 JSON 和 `Content-Type: application/json`。
成功响应为 HTTP `200`，直接返回下述字段，没有 `data` 包装。
`workingDir` 是服务约定的上下文选择参数，固定为 `/app/vbot-agent-harness`，
不是当前 shell 目录，也不代表有权写入该目录。
接口没有独立的 `/v1` 版本，兼容性以交付镜像为边界。

## 路由与数据结构

| 方法与路由 | Query／JSON body | 成功响应 |
| --- | --- | --- |
| `GET /api/skills` | Query `workingDir` | `{skills:[{name,description,source,path,shadowedByProject}]}` |
| `GET /api/skills/{name}` | Query `workingDir` | `{name:string,content:string,resources:string[]}` |
| `PUT /api/skills/{name}` | Body `{target:"user",content:string,workingDir?:string}` | `{path:string}` |
| `DELETE /api/skills/{name}` | Query `target=user` | `{deleted:true}` |
| `GET /api/agents-md` | Query `workingDir` | `{path:string,exists:boolean,content:string}` |
| `PUT /api/agents-md` | Body `{workingDir:string,content:string}`；`workingDir` 非空 | `{path:string}` |

Skill 名称只使用小写字母、数字与连字符。`content` 是完整的 `SKILL.md`，
包含 YAML frontmatter 和非空触发说明 `description`；其中 `name` 与路由名称保持一致。
EDU 写入、删除只使用 `target=user`。PUT 替换 `SKILL.md`，不接收目录压缩包，
也不支持任意资源上传。DELETE 删除整个用户 Skill 目录及其辅助文件，不只是 `SKILL.md`。

列表项中的 `name`、`description`、`source`、`path` 为字符串，`shadowedByProject` 为布尔值。
目录可能包含多层内容，请检查目标项的来源与优先级：同名项可能遮蔽用户 Skill。
单个 Skill 的 GET 返回按优先级解析后的内容，不是指定 target 的备份接口。
优先使用独有名称，不覆盖或删除归属不明的内容。

AGENTS.md PUT 原子替换整个用户层文本，不是追加。
GET 的 `exists` 可能反映兼容性回填内容，不能单凭它证明物理用户文件存在；
GET 也不是最终合并后的系统提示。没有公开的 AGENTS.md DELETE。
写入 `""` 表示清空用户内容，不是删除文件，也不会移除服务的基线指令。

## 准备环境，先读后写

以下是依赖 `curl`、`jq` 的 Bash 命令，不是仓库安装器。
在同一个 shell 中先执行一次准备步骤。所有请求都有超时，不自动重试。
仅在单独获准的访问入口或本地测试中覆盖 `VBOT_API_URL`。

```bash
set -euo pipefail

VBOT_API_URL="${VBOT_API_URL:-http://192.168.127.10:8787}"
VBOT_WORKING_DIR=/app/vbot-agent-harness
VBOT_BACKUP_DIR=$(mktemp -d)
vbot_curl() {
  curl --noproxy '*' -fsS --connect-timeout 3 --max-time 10 "$@"
}

vbot_curl --get "$VBOT_API_URL/api/skills" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_BACKUP_DIR/skills-before.json"
jq . "$VBOT_BACKUP_DIR/skills-before.json"
printf 'Keep content backups at: %s\n' "$VBOT_BACKUP_DIR"
```

使用示例名称 `campus-guide` 前先检查目录。不存在时可继续创建；
如果已存在、确属自己且解析来源是自己的用户内容，应先备份再替换。
否则请换一个名称，并同步修改编写文件及下方所有命令。

仅对已确认属于自己的现有 Skill 执行此备份步骤：

```bash
vbot_curl --get "$VBOT_API_URL/api/skills/campus-guide" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_BACKUP_DIR/campus-guide-before.json"
jq . "$VBOT_BACKUP_DIR/campus-guide-before.json"
```

JSON 备份只保存返回的文本与资源名称，不包含辅助文件正文；如有资源包，请另行保留原件。
删除任何内容前，须将备份保存到自己的持久、私密存储中；临时目录不是长期备份。
不要把个人内容或备份加入 vbot-lab。

## 上传设备 Skill 并检查读回

在自己的工作区将 [Skill 示例](customization.zh-CN.md)保存为 `./campus-guide/SKILL.md`，并先审阅。
示例开放时间是虚构数据。下面命令将创建 Skill 或替换其完整入口文本：

```bash
jq -n --rawfile content ./campus-guide/SKILL.md \
  --arg workingDir "$VBOT_WORKING_DIR" \
  '{target:"user",workingDir:$workingDir,content:$content}' |
  vbot_curl -X PUT "$VBOT_API_URL/api/skills/campus-guide" \
    -H 'Content-Type: application/json' --data-binary @- |
  jq -e 'select(.path == "/userdata/.vbot/content/user/skills/campus-guide/SKILL.md")'

vbot_curl --get "$VBOT_API_URL/api/skills/campus-guide" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" |
  jq -e --rawfile expected ./campus-guide/SKILL.md \
    '.name == "campus-guide" and .content == $expected'
```

预期输出通过路径检查的 `{path:...}` 响应，以及内容一致性检查的 `true`。
EDU 适配镜像的返回路径必须位于 `/userdata/.vbot/content/user/skills/` 下。
路径不符表示适配检查失败，应停止后续写入并联系平台方，不尝试直接修复文件系统。
即使路径检查失败，服务也可能已经完成写入。

## 备份、替换并读取 AGENTS.md

在自己的工作区将[指令示例](customization.zh-CN.md)保存为 `./device-AGENTS.md`，并先审阅。
不要上传 vbot-lab 的维护用 `AGENTS.md`。先获取 API 当前可见内容并审阅备份：

```bash
vbot_curl --get "$VBOT_API_URL/api/agents-md" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_BACKUP_DIR/agents-md-before.json"
jq . "$VBOT_BACKUP_DIR/agents-md-before.json"
```

审阅并保留备份后，明确执行用户层文本替换：

```bash
jq -n --arg workingDir "$VBOT_WORKING_DIR" \
  --rawfile content ./device-AGENTS.md \
  '{workingDir:$workingDir,content:$content}' |
  vbot_curl -X PUT "$VBOT_API_URL/api/agents-md" \
    -H 'Content-Type: application/json' --data-binary @- |
  jq -e 'select(.path == "/userdata/.vbot/content/user/AGENTS.md")'

vbot_curl --get "$VBOT_API_URL/api/agents-md" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" |
  jq -e --rawfile expected ./device-AGENTS.md \
    '.exists == true and .content == $expected'
```

预期输出通过路径检查的 `{path:...}` 响应和 `true`。
写入返回路径必须为 `/userdata/.vbot/content/user/AGENTS.md`；
不符时视为适配失败，不能据此直接修改服务文件。请保留备份。

## 行为验证、删除与恢复

每次内容修改后开启新 Turn。对 Skill，提出明确匹配 description 的无副作用问题，
观察实际激活及内容使用。若使用工具白名单，须保留交付服务的 Skill 激活工具，
不要使用空工具会话。对 AGENTS.md，观察指定回答规则是否生效。
保存／读回成功不能证明这两类行为，已运行的 Turn 也不保证热加载。两类指令都不是强制安全措施。

删除是可选的破坏性操作。确认 Skill 属于自己且已另行备份所有辅助文件后，
设置 `CONFIRM_SKILL_DELETE=campus-guide`，再执行以下命令删除该用户 Skill 目录：

```bash
[[ "${CONFIRM_SKILL_DELETE:-}" == campus-guide ]]
vbot_curl -X DELETE "$VBOT_API_URL/api/skills/campus-guide?target=user" |
  jq -e '.deleted == true'
```

删除后重新查询目录：删除用户项不代表其他层的同名项消失。
恢复文本时，审阅备份中的 `content`，再通过对应 PUT API 写回；这不会恢复辅助文件。
对 AGENTS.md，PUT 可恢复 API 可见文本，但不能恢复“原本没有物理文件”的状态，空写入也不等于删除。
恢复后在新 Turn 中验证行为。

| 失败／风险 | 处理要求 |
| --- | --- |
| 非 2xx／响应格式不符 | 保留 HTTP 状态，安全检查 Content-Type 和正文；错误不一定是 JSON |
| Skill 不存在 | 当前文档实现可能返回 `500`、`extension_failed`、`retryable=false`，不能假设一定返回 `404`，也不能对所有 5xx 循环重试 |
| `error.retryable` 缺失或为 false | 不能推定允许重试；只对明确的瞬时故障进行有界退避的只读重试 |
| PUT／DELETE 超时 | 结果未知；先查询目录／内容，再决定下一步，不盲目重发 |
| 并发修改 | 没有 ETag／If-Match 并发控制承诺；协调单写者，避免覆盖期间的新修改 |
| 交付镜像中 API 不可用 | 联系平台方确认支持版本，不从客户端修改服务配置 |

继续按[接入指南](../../guides/agent-integration.zh-CN.md)在新 Turn 使用内容。
更新内容无需重启或升级设备；不要在上传内容时修改系统服务或触发机器人运动。
