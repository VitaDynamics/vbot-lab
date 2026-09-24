# HTTP MCP 工具契约

<p align="center"><a href="http-mcp.md">English</a> | 中文</p>

适用范围及兼容性见 [Agent 能力总览](README.zh-CN.md)。
开发者在 S100 上以 `vbot` 身份运行服务，EDU 运行时作为 MCP 客户端。
这是 HTTP 请求／响应接口，不是 Aorta 或 ROS2 pub/sub。

## 地址与协议

| 项目 | 契约 |
| --- | --- |
| 设备入口 | `http://192.168.127.2:18080/mcp` |
| 传输方式 | HTTP POST，承载 JSON-RPC `2.0` |
| 协议版本 | `2025-06-18` |
| 请求 Content-Type | `application/json` |
| 请求 Accept | `application/json, text/event-stream` |
| 版本请求头 | `MCP-Protocol-Version: 2025-06-18` |
| 可选传输会话 | 初始化返回 `Mcp-Session-Id` 时，后续请求须携带 |
| 开发环境 | S100、`vbot` 账户、可写用户目录 `/userdata/vbot` |

固定地址是本 EDU 契约约定的开发者服务入口。
工作站回环地址只用于本地协议检查，不改变机器人运行时连接的目标。
设备服务应监听约定的内部网卡，不得将服务暴露或转发到不可信网络、校园公网或互联网。

## 支持的方法

| JSON-RPC method | 请求 | 响应 |
| --- | --- | --- |
| `initialize` | 带 `id`，`params` 含 `protocolVersion`、`capabilities`、`clientInfo` | `result.protocolVersion`、`result.capabilities.tools`、`result.serverInfo`；可选 `Mcp-Session-Id` 响应头 |
| `notifications/initialized` | 初始化成功后发送，不含 `id` 的通知 | 本指南检查 HTTP `202` 空正文；其他空成功响应须按实际固件版本验证 |
| `tools/list` | 带 `id`，`params` 为空对象 | `result.tools[]`，每项含 `name`、`description`、`inputSchema` |
| `tools/call` | 带 `id`、`params.name`、`params.arguments` | `result.content[]`；工具执行失败用 `result.isError=true` |

顺序为初始化、发送 `notifications/initialized`、列举工具、调用工具。
初始化返回会话 ID 时，包括通知在内的后续请求均携带该 ID，并携带协商后的协议版本。
版本不兼容或缺少工具能力时不要继续调用。这些生命周期规则参照固定版本的
[MCP 生命周期](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)与
[HTTP 传输规范](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)。

即使通用 MCP 框架支持 Resources、Prompts 或 stdio transport，
它们仍不属于当前 EDU 开发契约。

## 工具定义与返回值

`edu_echo` 与 `edu_add` 是本指南使用的无副作用演示工具，不是机器人内置控制 API。
本仓库尚未交付这两个工具的可执行代码。业务逻辑应使用 MCP 原始工具名与 Schema，不依赖界面展示名。

`edu_add` 定义如下：

```json
{
  "name": "edu_add",
  "description": "Add two numbers and return the result.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "a": {"type": "number"},
      "b": {"type": "number"}
    },
    "required": ["a", "b"],
    "additionalProperties": false
  }
}
```

`edu_echo` 要求字符串参数 `message`，并拒绝额外属性。
描述应说明何时调用、返回什么；服务端自行校验必填参数、类型、范围与枚举。
声明 JSON Schema 不等于实现已经执行了校验。

请求示例：

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"edu_add","arguments":{"a":1,"b":2}}}
```

成功响应示例：

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [{"type": "text", "text": "{\"value\": 3.0}"}],
    "structuredContent": {"value": 3.0},
    "isError": false
  }
}
```

`structuredContent` 是可选输出示例，不是新增的 EDU 通用必选字段。
应保留可用的 `content` 并检查 `isError`，HTTP `200` 不等于工具成功。
协议错误使用 JSON-RPC `error` 对象；工具执行失败保留可操作的错误信息，并设置 `isError=true`，参见
[MCP 工具结果契约](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)。

## 服务端责任

- 支持重复初始化，限制请求体大小与等待时间，避免不安全的重试。
- 产生副作用前校验权限和输入；按需加入幂等键、审计、超时及确认，不将无限制 Shell 当作演示工具开放。
- 根据实际部署评估 Origin 校验与鉴权。协议示例不提供完整的生产安全实现，参阅
  [HTTP 传输安全要求](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)。
- `/healthz` 等本地健康检查是可选诊断入口，不是 MCP 方法，也不能证明 Agent 已发现工具。

下一步阅读[接入指南](../../guides/agent-integration.zh-CN.md)。
