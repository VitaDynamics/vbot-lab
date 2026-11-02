# 配置外部 MCP 服务

<p align="center"><a href="mcp-config.md">English</a> | 中文</p>

通过这些 HTTP API，可以为设备 Agent 新增 **Streamable HTTP MCP** 服务连接，
或编辑、启用和停用已有连接，无需重启设备。
适用范围及应用兼容性见 [Agent 概览](README.zh-CN.md)。
这些是配置 API，不是 MCP JSON-RPC 方法，也不是 Aorta 路由。

## 连接与作用范围

在 S100 的 `vbot` SSH 终端运行命令，需具备 `curl`、`jq`。
Agent API 基址为 `http://192.168.127.10:8787`，下列路由的统一前缀为
`/api/admin/extensions/vbot-mcp/http`。仅在可信机器人网络内使用，
不要将该 API 暴露或转发到不可信网络或互联网。

MCP `url` 是**设备运行时需要连接的目标**，不是上面的 API 基址。
可以指向你在 S100 上运行的服务，或其他可达且可信的 HTTP/HTTPS MCP 服务。
`localhost` 指 Agent 运行时所在机器，不是工作站，也不是 S100 SSH 终端所在机器。
连接另一台机器上的服务时，填写明确可达的地址。
服务需自行启动并维护；保存 URL 不会部署或拉起服务。

修改持久保存到设备运行时的全局配置，并作用于其各个工作区。
`workingDir` 与[内容 API](content-api.zh-CN.md)使用相同的运行时上下文选择值，
不代表允许访问该目录。写入、刷新和检查均使用同一上下文。
不要修改不属于自己的预置服务。

## 路由

下表路径均相对于 `/api/admin/extensions/vbot-mcp/http`。
请求及响应使用 JSON，没有 `data` 包装层。

| 方法与路径 | 请求 | 成功结果 |
| --- | --- | --- |
| `GET /servers` | 查询参数 `workingDir` | `200`：服务列表与发现状态 |
| `POST /servers` | 查询参数 `workingDir`；下文新增请求体 | `201`：更新后的服务列表，并在后台开始发现 |
| `GET /servers/{name}/config` | 查询参数 `workingDir` | `200`：可编辑配置，不返回已保存的请求头值 |
| `PUT /servers/{name}/config` | 查询参数 `workingDir`；下文编辑请求体 | `200`：更新后的列表，并在后台发现 |
| `PATCH /servers/{name}` | 查询参数 `workingDir`；`{"enabled":true}` 或 `{"enabled":false}` | `200`：更新后的列表，并在后台发现 |
| `POST /servers/refresh` | 查询参数 `workingDir`；无需请求体 | `200`：调度连接／目录刷新后的列表 |

目前没有删除服务定义或重命名 API。不再需要自己的连接时，通过 PATCH 停用；
定义及已保存的凭据仍保留。停用不等于删除、撤销凭据，也不等于取消正在执行的工具调用。
这些 API 不新增或编辑 stdio 进程定义，不安装软件包，也不执行 OAuth 登录。

### 新增字段

```json
{
  "name": "edu-tools",
  "type": "http",
  "url": "http://192.168.127.2:18081/mcp",
  "headers": {}
}
```

| 字段 | 含义与填写范围 |
| --- | --- |
| `name` | 必填，1–128 个 ASCII 字母、数字、`-` 或 `_`，至少包含一个字母或数字。规范化后的工具前缀也不能重复，例如 `edu-tools` 与 `EDU_TOOLS` 冲突。 |
| `type` | 必填，固定为 `"http"`；表示 Streamable HTTP，不是旧版 HTTP+SSE 传输。 |
| `url` | 必填，HTTP/HTTPS 绝对地址，包含服务实际路径；不能嵌入用户名／密码或 URL fragment。 |
| `headers` | 可选，字符串到字符串的映射，默认 `{}`。Bearer 认证填写 `Authorization: "Bearer <实际 token>"`；API key 使用服务规定的请求头。值按原文发送，不展开 `${...}`。 |
| `envHttpHeaders` | 新增时省略或填 `{}`。API 不允许新增对运行时环境变量的引用。 |
| `protocolVersion` | 可选，运行时支持的 MCP 握手版本，不是软件包版本。通常省略以协商；[工具契约](http-mcp.zh-CN.md)使用的版本是 `"2025-06-18"`。 |

未知字段会被拒绝。请求头查重不区分大小写，不要同时填写 `Authorization` 与
`authorization`，也不要用固定值与环境引用重复配置同一个请求头。
不能覆盖由传输层管理的 `Content-Type`、`Accept`、`MCP-Protocol-Version`、
`MCP-Method`、`MCP-Name` 或 `Mcp-Session-Id`。
不要将凭据放入 URL、代码仓库、命令历史或共享日志。

### 读取与编辑字段

GET config 返回 `name`、`url`、`source`、不透明的 `revision`、`headerNames`、
`hasBearerToken` 和 `envHttpHeaders`，不返回已保存的固定请求头值。
列表中的 `target` 仅包含 HTTP origin；完整 URL 通过 GET config 获取。

PUT 必须包含下面四个字段，不接受 `name`、`type`、`enabled` 或 `protocolVersion`。
启停状态使用 PATCH，名称不可修改。

```json
{
  "revision": "<revision from a fresh GET config>",
  "url": "http://192.168.127.2:18081/mcp",
  "headers": {},
  "envHttpHeaders": {}
}
```

- `revision`：原样使用最新 GET 返回值。其他操作修改配置或运行时重启后可能失效；
  冲突时重新读取并核对，不要直接覆盖。
- `headers`：期望保留的完整集合。字符串表示替换／新增，`null` 表示保留该名称已有的值，
  省略某个请求头表示删除它，`{}` 表示清除全部固定请求头。不要把脱敏占位符当成真实凭据提交。
- `envHttpHeaders`：期望保留的已有环境引用完整集合。每个名称／值只能原样保留或省略以移除，
  新增或改写引用会被拒绝，`{}` 表示清除全部环境引用。
- URL 的协议、主机或端口改变时，必须重新填写或移除所有原样保留的固定请求头，
  并移除环境引用，防止将已保存的凭据发送到不同 origin。

遵循列表中的 `canEdit`。项目定义和 stdio 条目不能通过 PUT 编辑。
编辑可修改的安装包条目会创建全局覆盖，不会修改安装包原定义。
建议新增自己拥有且名称唯一的连接。

## 先读取，再注册服务

在同一个 Bash 终端完成一次准备。只有明确提交写入或刷新后，才会连接 MCP 服务；
GET 列表是只读操作。

```bash
set -euo pipefail

VBOT_API_URL="${VBOT_API_URL:-http://192.168.127.10:8787}"
VBOT_MCP_API_URL="$VBOT_API_URL/api/admin/extensions/vbot-mcp/http"
VBOT_WORKING_DIR=/app/vbot-agent-harness
VBOT_MCP_FILES=$(mktemp -d)
vbot_mcp_curl() {
  curl --noproxy '*' -fsS --connect-timeout 3 --max-time 35 "$@"
}

vbot_mcp_curl --get "$VBOT_MCP_API_URL/servers" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_MCP_FILES/servers-before.json"
jq . "$VBOT_MCP_FILES/servers-before.json"
jq -e '.canAddServers == true' "$VBOT_MCP_FILES/servers-before.json"
```

API 不可用或 `canAddServers` 不为 true 时停止。新增前先检查已有名称。
下面将注册**你已启动的服务**，执行前将示例地址、端口及路径替换为真实入口。
注册可能立即发起发现，因此只连接可信服务。示例服务不需要认证；
需要认证的服务应通过妥善准备的文件提供相应请求头。

```bash
vbot_mcp_curl -X POST "$VBOT_MCP_API_URL/servers?workingDir=$VBOT_WORKING_DIR" \
  -H 'Content-Type: application/json' \
  --data-binary '{"name":"edu-tools","type":"http","url":"http://192.168.127.2:18081/mcp","headers":{}}' |
  jq .
```

### 刷新与检查发现结果

新增、编辑及启停已会调度发现。服务恢复或工具定义改变后，可显式刷新；
它可能重新连接此上下文中的配置服务，不只影响 `edu-tools`。

```bash
vbot_mcp_curl -X POST "$VBOT_MCP_API_URL/servers/refresh?workingDir=$VBOT_WORKING_DIR" |
  jq .

vbot_mcp_curl --get "$VBOT_MCP_API_URL/servers" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" |
  jq '{catalogReady,catalogRevision,refreshPending,diagnostics,storageAvailable,loadError,
       servers:[.servers[] | select(.name == "edu-tools")]}'
```

`refreshPending=true` 时，等待后再次 GET，并设置等待总时限，不要反复 POST 刷新。
刷新结束后，应确认 `catalogReady=true`、自己的条目 `enabled=true`，
没有条目 `configError` 或相关发现诊断，且 `toolCount` 符合服务实际工具数量。
`storageAvailable` 表示启停状态存储情况；`canAddServers` 及条目 `canEdit`
表示配置操作能力。存在 `loadError` 时，先排查再继续写入。单独 GET 不会开始发现。

配置保存不代表连接成功，也不代表工具已执行。发现成功后，在新的 Agent Turn 中请求
调用一个无副作用工具，并在服务端确认实际结果。工具以规范化名称暴露，例如
`mcp__edu_tools__edu_echo`；直接 MCP `tools/call` 仍使用原始名称 `edu_echo`。
已有会话可在后续 Turn 获取刷新后的工具，不要假定正在执行的 Turn 或调用会立即改变。
会话的工具选择还需允许该工具。无需重启设备。

### 不暴露已保存凭据的编辑方式

读取新配置，构造完整编辑请求体，确认后再 PUT。
示例保留全部已有请求头及环境引用，URL 也保持不变；
需要修改设置时，先明确编辑 `edit.json`。

```bash
vbot_mcp_curl --get "$VBOT_MCP_API_URL/servers/edu-tools/config" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_MCP_FILES/config-before.json"
jq '{revision,url,
     headers:(.headerNames | map({key:.,value:null}) | from_entries),
     envHttpHeaders}' "$VBOT_MCP_FILES/config-before.json" > "$VBOT_MCP_FILES/edit.json"
jq . "$VBOT_MCP_FILES/edit.json"

# After reviewing the complete edit body:
vbot_mcp_curl -X PUT "$VBOT_MCP_API_URL/servers/edu-tools/config?workingDir=$VBOT_WORKING_DIR" \
  -H 'Content-Type: application/json' --data-binary "@$VBOT_MCP_FILES/edit.json" |
  jq .
```

随后再次 GET config 核对 URL 与请求头名称，再检查发现结果，并在新 Turn 中执行无副作用调用。
脱敏读回不是凭据备份：原始凭据需在仓库之外妥善保存。
若本地编辑文件包含新填入的凭据，使用后妥善保护并移除。

### 停用或重新启用自己的连接

```bash
vbot_mcp_curl -X PATCH "$VBOT_MCP_API_URL/servers/edu-tools?workingDir=$VBOT_WORKING_DIR" \
  -H 'Content-Type: application/json' --data-binary '{"enabled":false}' |
  jq .
```

将请求体改为 `{"enabled":true}` 可重新启用同一连接。
操作后读取列表，确认刷新结束后的状态。不要启停无关服务。

## 错误与恢复

| 结果 | 处理方式 |
| --- | --- |
| `400 mcp_server_invalid_body`／`mcp_server_invalid_config` | 检查必填字段、URL、名称、请求头规则，以及新增与编辑请求体的区别；不要重试相同错误输入。 |
| `409 mcp_server_already_exists` | 名称或规范化工具前缀冲突，先读列表，再选择不同名称；POST 不覆盖已有条目。 |
| `409 mcp_server_config_changed` | 重新读取配置／revision，对比修改后重建完整编辑请求。 |
| `404 mcp_server_not_found` | 刷新列表并确认准确名称及上下文，不要据此判断整组 API 不可用。 |
| `405 mcp_server_read_only` | 遵循来源／传输类型与 `canEdit`，新增自己的 HTTP 条目，不要修改受保护定义。 |
| `500 mcp_config_write_failed`／`mcp_server_state_write_failed`，或 `503 mcp_config_unavailable` | 保留错误并联系支持，不要通过修改设备权限或覆盖配置文件绕过 API。 |
| 非 2xx、超时或写入中断 | 安全检查状态码／正文，先 GET 列表及配置，再决定是否重试；写入可能已落盘，不要盲目重复 POST／PUT。 |
| 保存后没有工具 | 检查 `enabled`、刷新是否结束、`configError`、诊断、设备到服务的网络、认证、MCP 传输及工具声明；没有工具的服务不能满足工具调用需求。 |

继续阅读[工具契约](http-mcp.zh-CN.md)及[接入指南](../../guides/agent-integration.zh-CN.md)。
设备端 Skills 与 `AGENTS.md` 使用独立的[内容 API](content-api.zh-CN.md)，不是 MCP 服务定义。
