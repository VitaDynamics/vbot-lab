# Agent 接入

<p align="center"><a href="agent-integration.md">English</a> | 中文</p>

先阅读 [Agent 契约](../interfaces/agent/README.zh-CN.md)。
当前设备范围为 `foot_quadruped`、S100、单可信开发者及 `vbot` 账户。
接入前请确认当前设备固件及运行时版本的兼容性。

## 准备开发者服务

仅新增 MCP 工具时需要本节。若只注入设备端 Skill 或 AGENTS.md，可直接阅读
[内容 API 准备步骤](../interfaces/agent/content-api.zh-CN.md)，不需要运行开发者自建的 MCP 服务。

自行提供满足 [HTTP MCP 契约](../interfaces/agent/http-mcp.zh-CN.md)的服务，
以 `vbot` 身份监听约定内网地址 `192.168.127.2:18080`，开发者文件位于 `/userdata/vbot`。
使用 `vbot` 账户及其已分配的权限。先确认端口可用，不要为占用端口终止未知服务或改动系统服务。

以下检查要求服务提供 `edu_echo`、`edu_add` 两个无副作用演示工具，请求与响应格式见接口契约。
不要将检查直接用于有实际副作用的任意工具。
本仓库目前尚未包含这些工具的可执行实现。

若你的服务提供 `/healthz` 接口，可先检查它。
该接口是可选项，不能证明 MCP 工具发现或 Agent 接入已通过。

## 检查完整 MCP 交互

服务已监听后，在装有 `curl`、`jq` 的 S100 Bash 终端执行。
脚本默认访问约定设备入口；仅进行独立本地协议检查时覆盖 `MCP_URL`。
脚本不会启动、安装或配置服务。

检查要求返回本文示例格式的 JSON，初始化通知返回 HTTP `202`。
它不是 SSE 解码器：若响应为 `text/event-stream`，应使用兼容的 MCP 客户端验证相同顺序。
若交付版本允许其他空成功状态码，单独验证该行为，不要直接忽略所有状态码。

```bash
set -euo pipefail

MCP_URL="${MCP_URL:-http://192.168.127.2:18080/mcp}"
MCP_HEADER_FILE=$(mktemp)
MCP_BODY_FILE=$(mktemp)
trap 'unlink "$MCP_HEADER_FILE"; unlink "$MCP_BODY_FILE"' EXIT

MCP_HEADERS=(
  -H 'Content-Type: application/json'
  -H 'Accept: application/json, text/event-stream'
  -H 'MCP-Protocol-Version: 2025-06-18'
)

curl -fsS --connect-timeout 3 --max-time 10 \
  -D "$MCP_HEADER_FILE" -o "$MCP_BODY_FILE" \
  "${MCP_HEADERS[@]}" "$MCP_URL" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"edu-test","version":"1.0"}}}'

jq -e '.jsonrpc == "2.0" and .id == 1 and
  .result.protocolVersion == "2025-06-18" and
  (.result.capabilities.tools | type == "object") and
  (.result.serverInfo.name | type == "string")' "$MCP_BODY_FILE"

MCP_SESSION_ID=$(awk 'tolower($1) == "mcp-session-id:" {
  gsub("\r", "", $2); print $2
}' "$MCP_HEADER_FILE")
if [[ -n "$MCP_SESSION_ID" ]]; then
  MCP_HEADERS+=(-H "Mcp-Session-Id: $MCP_SESSION_ID")
fi

MCP_NOTIFY_STATUS=$(curl -fsS --connect-timeout 3 --max-time 10 \
  -o "$MCP_BODY_FILE" -w '%{http_code}' \
  "${MCP_HEADERS[@]}" "$MCP_URL" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}')
[[ "$MCP_NOTIFY_STATUS" == 202 && ! -s "$MCP_BODY_FILE" ]]

curl -fsS --connect-timeout 3 --max-time 10 \
  "${MCP_HEADERS[@]}" "$MCP_URL" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' |
  jq -e '.jsonrpc == "2.0" and .id == 2 and
    any(.result.tools[]; .name == "edu_echo" and .inputSchema.type == "object") and
    any(.result.tools[]; .name == "edu_add" and .inputSchema.type == "object")'

curl -fsS --connect-timeout 3 --max-time 10 \
  "${MCP_HEADERS[@]}" "$MCP_URL" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"edu_echo","arguments":{"message":"hello EDU"}}}' |
  jq -e '.jsonrpc == "2.0" and .id == 3 and .result.isError == false and
    any(.result.content[]; .type == "text" and (.text | fromjson | .message == "hello EDU"))'

curl -fsS --connect-timeout 3 --max-time 10 \
  "${MCP_HEADERS[@]}" "$MCP_URL" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"edu_add","arguments":{"a":1,"b":2}}}' |
  jq -e '.jsonrpc == "2.0" and .id == 4 and .result.isError == false and
    any(.result.content[]; .type == "text" and (.text | fromjson | .value == 3))'

printf '%s\n' 'MCP protocol smoke check passed.'
```

预期输出四个 `true`，最后输出 `MCP protocol smoke check passed.`。
通知也会检查 HTTP `202` 和空正文。
协议错误、返回值不符、`isError=true` 或非 JSON 正文都会使检查失败。
退出时分别删除临时响应头／正文文件；不要分享包含会话请求头的日志。

curl 检查通过仅证明开发者服务能处理这些请求。
随后在 Agent 中发起一个应使用 `edu_echo` 或 `edu_add` 的新请求，
同时确认返回结果及开发者服务端确实收到调用。`tools/list` 用于发现工具，再通过无副作用调用确认执行正常。

## 导入并验证定制内容

1. 在自己的工作区编写并审阅[设备端 Skills 与 AGENTS.md](../interfaces/agent/customization.zh-CN.md)，
   不放入仓库的 Coding Agent `skills/` 目录。
2. 按[内容 API](../interfaces/agent/content-api.zh-CN.md)查询／备份现有内容、上传、检查返回持久路径并比较读回文本。
3. 开启新 Turn，观察 Skill 激活／指令行为。使用白名单时保留交付服务的 Skill 激活工具，不能使用空工具会话。
4. 在自己的工作区保留已上传内容及原内容备份；需要恢复时，通过同一 API 写回，并开启新 Turn。

## 错误、重试与副作用

| 现象 | 处理方式 |
| --- | --- |
| 初始化失败 | 检查监听地址、端口、协议版本、响应 Content-Type 与 JSON-RPC 格式，不通过公网开放端口排障 |
| HTTP `404` 或 `408` | 先检查服务、路径和日志，再进行有限次数退避重试；会话过期时，不带旧会话请求头重新初始化 |
| `tools/call` 返回 HTTP `200`，但 `isError=true` | 保留并分析业务错误，不报告成功 |
| 有副作用的调用超时 | 核实前视为结果未知，避免盲目重试，结合幂等键和审计记录处理 |
| Skill 或 AGENTS.md 无可观察效果 | 检查 API 读回、返回路径、内容优先级及 Skill 激活工具可用性；在新 Turn 验证触发条件／规则 |

机器人运动、文件修改或外部服务调用工具须实现服务端权限校验、参数范围、幂等、超时、审计及必要确认。
执行已授权的运动操作前，应清空周围环境并准备物理急停；软件取消或超时不能替代硬件急停。

## 完成接入

- 使用 MCP 时，保持自己的服务运行，并确认 Agent 发起的无副作用工具调用返回预期结果。
  发现或执行失败时按上表排查。
- 使用 Skill 或 AGENTS.md 时，确认 API 读回与预期内容一致，再开启新 Turn 使用；
  保留备份，便于后续修改与恢复。
- 将 `18080` 与 `8787` 端口保留在可信网络内，不暴露或转发至校园公网或互联网。

本接入流程不需要重启或升级设备。
