# Agent integration

<p align="center">English | <a href="agent-integration.zh-CN.md">中文</a></p>

Read the [Agent contract](../interfaces/agent/README.md) first.
The current device scope is `foot_quadruped`, S100, one trusted developer, and the
`vbot` account. Check compatibility with your device's firmware and runtime version before integration.

## Prepare the developer service

This section is needed only when adding MCP tools. To inject a device Skill or
AGENTS.md without adding tools, go directly to [content API preparation](../interfaces/agent/content-api.md).
No developer-owned MCP server is required for content API calls.

Provide your own service implementing the [HTTP MCP contract](../interfaces/agent/http-mcp.md).
Run it as `vbot` on the agreed internal address `192.168.127.2:18080`, with
developer files under `/userdata/vbot`. Use the `vbot` account and its assigned permissions.
Ensure the port is available; do not kill an unknown listener or alter system services to claim it.

The checks below assume a server exposing two harmless demonstration tools, `edu_echo`
and `edu_add`, with the request and response shapes documented in the contract.
Do not run the checks against arbitrary tools with real-world side effects.
An executable implementation of these tools is not yet included in this repository.

If your service provides a `/healthz` endpoint, check it first.
This endpoint is optional and does not establish MCP discovery or Agent integration.

## Check the complete MCP exchange

Run the following in Bash on S100 with `curl` and `jq` installed, after your service is listening.
The script defaults to the agreed device endpoint; override `MCP_URL` only for a separate
local protocol test. It does not start, install, or configure a service.

This check expects the documented example JSON responses and HTTP `202` for
the initialization notification. It is not an SSE decoder: for `text/event-stream`
responses, use a compatible MCP client and validate the same sequence.
If the delivered version permits another empty notification success status, validate
that behavior separately instead of ignoring all status codes.

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

Expected output is four `true` assertions followed by `MCP protocol smoke check passed.`.
The notification is also checked for HTTP `202` and an empty body.
A protocol error, wrong result, `isError=true`, or non-JSON body fails the check.
Temporary header / body files are removed separately on exit; do not share session headers in logs.

Passing curl checks proves only that the developer server handles those requests.
Next, issue a new Agent request that should use `edu_echo` or `edu_add`,
and verify both the returned result and an observed call in the developer service.
Successful `tools/list` discovers tools; use a harmless call to check their execution.

## Import and validate customization

1. Write and review [device Skills and AGENTS.md](../interfaces/agent/customization.md)
   in your own workspace, not the repository's Coding Agent `skills/` directory.
2. Follow the [content API](../interfaces/agent/content-api.md) to inspect / back up
   current content, upload it, check the returned persistent path, and compare readback.
3. Start a new Turn and observe Skill activation / instruction behavior. Retain the
   delivered Skill activation tool if using an allowlist; an empty-tool session is unsuitable.
4. Keep a copy of the uploaded content and its backup in your own workspace. If the content
   needs restoring, use the same API to write it back and start a new Turn.

## Errors, retries, and side effects

| Symptom | Action |
| --- | --- |
| Initialization fails | Check listener address, port, protocol version, response Content-Type, and JSON-RPC format; do not expose the port publicly for diagnosis |
| HTTP `404` or `408` | Check service health, path, and logs first; use bounded retries with backoff. If a session expired, initialize again without the old session header |
| `tools/call` returns HTTP `200` with `isError=true` | Preserve and inspect the business error; do not report success |
| Timeout on a side-effecting call | Treat the outcome as unknown until checked; avoid blind retries, use idempotency and audit records |
| Skill or AGENTS.md has no observable effect | Check API readback, returned path, content precedence, and Skill activation-tool availability; test the intended trigger / rule in a new Turn |

Tools that move the robot, modify files, or call external services need server-side
authorization, argument limits, idempotency, timeouts, audit, and appropriate confirmation.
Before an authorized motion operation, clear the surroundings and prepare the physical emergency stop.
Software cancellation or timeout is not a substitute for it.

## Complete the integration

- For MCP, keep your service running and confirm a harmless tool call from the Agent returns
  the expected result. Use the error table above if discovery or execution fails.
- For Skills or AGENTS.md, confirm API readback matches the intended content, then start a
  new Turn to use it. Keep backups for later edits and restoration.
- Keep ports `18080` and `8787` on the trusted network; do not expose or forward them to
  campus public networks or the Internet.

Rebooting or upgrading the device is not part of this integration procedure.
