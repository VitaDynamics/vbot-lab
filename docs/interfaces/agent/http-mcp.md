# HTTP MCP tool contract

<p align="center">English | <a href="http-mcp.zh-CN.md">中文</a></p>

Scope and compatibility follow the [Agent capability overview](README.md).
The developer runs the server on S100 as `vbot`; the EDU runtime is the MCP client.
This is an HTTP request / response interface, not Aorta or ROS2 pub/sub.

## Endpoint and protocol

| Item | Contract |
| --- | --- |
| Device endpoint | `http://192.168.127.2:18080/mcp` |
| Transport | HTTP POST carrying JSON-RPC `2.0` |
| Protocol version | `2025-06-18` |
| Request Content-Type | `application/json` |
| Request Accept | `application/json, text/event-stream` |
| Version header | `MCP-Protocol-Version: 2025-06-18` |
| Optional transport session | Preserve `Mcp-Session-Id` if returned by initialization |
| Environment | S100, `vbot` account, writable user directory `/userdata/vbot` |

The fixed address is the agreed developer-service endpoint for this EDU contract.
Workstation loopback addresses are for local
protocol testing only and do not change where the robot runtime connects.
Keep the device listener on the agreed internal interface; do not expose or forward
the service to untrusted networks, campus public networks, or the Internet.

## Supported methods

| JSON-RPC method | Request | Response |
| --- | --- | --- |
| `initialize` | An `id` and `params` containing `protocolVersion`, `capabilities`, and `clientInfo` | `result.protocolVersion`, `result.capabilities.tools`, and `result.serverInfo`; optionally an `Mcp-Session-Id` response header |
| `notifications/initialized` | Notification with no `id`, sent after successful initialization | HTTP `202` with an empty body for this guide's checks; validate other empty success responses against your firmware version |
| `tools/list` | An `id` and empty `params` | `result.tools[]`, including each tool's `name`, `description`, and `inputSchema` |
| `tools/call` | An `id`, `params.name`, and `params.arguments` | `result.content[]`; use `result.isError=true` for a tool execution failure |

Initialize first, send `notifications/initialized`, then list and call tools.
When initialization returns a session ID, send it on subsequent requests, including the notification.
Keep the negotiated protocol version on subsequent requests. Do not continue after an incompatible
version or missing tool capability. These lifecycle rules follow the pinned
[MCP lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle) and
[HTTP transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports) specifications.

Resources, Prompts, and stdio transport are outside
the EDU contract even if a general-purpose MCP framework supports them.

## Tool definitions and results

`edu_echo` and `edu_add` are side-effect-free demonstration tools used in this guide,
not built-in robot-control APIs. They are not shipped as executable code in this repository.
Use raw MCP tool names and their declared schemas, not UI display names.

The `edu_add` definition is:

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

For `edu_echo`, require a string argument named `message` and reject additional properties.
Descriptions should explain when to call the tool and what it returns.
Validate required arguments, types, ranges, and enums in the server; declaring a JSON Schema
does not itself enforce it in your implementation.

Example request:

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"edu_add","arguments":{"a":1,"b":2}}}
```

Example success response:

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

`structuredContent` is shown as optional example output, not as an additional EDU-wide
requirement. Keep `content` usable and inspect `isError`; HTTP `200` alone is not tool success.
Protocol errors use a JSON-RPC `error` object. Tool execution failures should retain useful
error details in `content` and set `isError=true`, as described by the
[MCP tool-result contract](https://modelcontextprotocol.io/specification/2025-06-18/server/tools).

## Server responsibilities

- Handle repeat initialization and bounded request sizes / timeouts without unsafe retries.
- Validate authorization and input before side effects. Add idempotency keys, audit records,
  timeouts, and confirmation where necessary; do not expose an unrestricted shell as a demo tool.
- Review Origin validation and authentication for the actual deployment. Protocol examples
  do not provide a complete production security implementation; see the
  [HTTP transport security guidance](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).
- A local health check such as `/healthz` is an optional diagnostic endpoint,
  not an MCP method or proof that the Agent has discovered your tools.

Continue with the [integration guide](../../guides/agent-integration.md).
