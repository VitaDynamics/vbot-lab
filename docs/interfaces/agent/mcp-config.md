# Configure external MCP services

<p align="center">English | <a href="mcp-config.zh-CN.md">中文</a></p>

Use these HTTP APIs to connect the device Agent to additional **Streamable HTTP MCP**
services, or edit, enable and disable existing connections without restarting the device.
Scope and application compatibility follow the [Agent overview](README.md).
These are configuration APIs, not MCP JSON-RPC methods or Aorta routes.

## Connection and scope

Run the commands in a `vbot` SSH shell on S100, with `curl` and `jq` available.
The Agent API base is `http://192.168.127.10:8787`; all routes below use the prefix
`/api/admin/extensions/vbot-mcp/http`. Use only a trusted robot network; do not expose
or forward this API to untrusted networks or the Internet.

The MCP `url` is a **destination the device runtime must reach**, not the API base above.
It may point to your S100 service or another reachable, trusted HTTP/HTTPS MCP service.
`localhost` refers to the machine running the Agent runtime, not your workstation or
the S100 SSH shell. Use an explicit reachable address for a service on another machine.
Start and maintain that service yourself; saving its URL does not deploy or launch it.

Changes persist in the device runtime's global configuration and apply across its
workspaces. `workingDir` selects the same runtime context as the
[content API](content-api.md); it is not permission to access that directory.
Use that same context for writes, refreshes and checks. Do not change preconfigured
services that you do not own.

## Routes

Paths in this table are relative to `/api/admin/extensions/vbot-mcp/http`.
Requests and responses use JSON, without a `data` wrapper.

| Method and path | Request | Success |
| --- | --- | --- |
| `GET /servers` | Query `workingDir` | `200`: server list and discovery state |
| `POST /servers` | Query `workingDir`; create body below | `201`: updated server list; discovery starts in the background |
| `GET /servers/{name}/config` | Query `workingDir` | `200`: editable configuration with saved header values redacted |
| `PUT /servers/{name}/config` | Query `workingDir`; edit body below | `200`: updated server list; background discovery |
| `PATCH /servers/{name}` | Query `workingDir`; `{"enabled":true}` or `{"enabled":false}` | `200`: updated server list; background discovery |
| `POST /servers/refresh` | Query `workingDir`; no body required | `200`: list after scheduling a connection/catalog refresh |

There is no server-definition DELETE or rename API. Disable your connection with
PATCH when it is no longer needed; this retains the definition and saved credentials.
Disabling is not deletion, credential revocation, or cancellation of an already-running
tool call. These APIs do not add or edit stdio process definitions, install packages,
or perform an OAuth login.

### Create fields

```json
{
  "name": "edu-tools",
  "type": "http",
  "url": "http://192.168.127.2:18081/mcp",
  "headers": {}
}
```

| Field | Meaning and allowed values |
| --- | --- |
| `name` | Required, 1–128 ASCII letters, digits, `-` or `_`, including at least one letter or digit. Names must also have distinct normalized tool prefixes: `edu-tools` and `EDU_TOOLS` conflict. |
| `type` | Required, exactly `"http"`; Streamable HTTP, not the legacy HTTP+SSE transport. |
| `url` | Required absolute HTTP/HTTPS URL, including the service's actual path. No embedded username/password or URL fragment. |
| `headers` | Optional string-to-string map, default `{}`. For Bearer authentication use `Authorization: "Bearer <actual-token>"`; API keys use the service's documented header. Values are literal, not `${...}` substitutions. |
| `envHttpHeaders` | Omit or use `{}` on creation. New references to runtime environment variables cannot be introduced through this API. |
| `protocolVersion` | Optional MCP handshake version supported by the runtime, not a package version. Normally omit it for negotiation; `"2025-06-18"` is the version used by the [tool contract](http-mcp.md). |

Unknown fields are rejected. Header names are case-insensitive for duplicate checking;
do not supply both `Authorization` and `authorization`, or duplicate a fixed header with
an environment reference. Do not override the transport-owned headers `Content-Type`,
`Accept`, `MCP-Protocol-Version`, `MCP-Method`, `MCP-Name` or `Mcp-Session-Id`.
Keep credentials out of URLs, source control, command history and shared logs.

### Read and edit fields

GET config returns `name`, `url`, `source`, opaque `revision`, `headerNames`,
`hasBearerToken` and `envHttpHeaders`. It never returns saved fixed header values.
The list's `target` contains only the HTTP origin; use GET config to read the full URL.

PUT requires all four fields below. It does not accept `name`, `type`, `enabled` or
`protocolVersion`; use PATCH for enabled state. The name cannot be changed.

```json
{
  "revision": "<revision from a fresh GET config>",
  "url": "http://192.168.127.2:18081/mcp",
  "headers": {},
  "envHttpHeaders": {}
}
```

- `revision`: use the latest GET value unchanged. A concurrent edit or runtime restart
  can invalidate it; on conflict, fetch again and review rather than overwrite.
- `headers`: the complete desired set. A string replaces/adds a value; `null` retains
  an existing value with that name; omitting a header removes it. `{}` removes all
  fixed headers. Do not send a masked placeholder as a real credential.
- `envHttpHeaders`: the complete desired set of already-provisioned references.
  Retain each name/value pair unchanged or omit it to remove it; new or altered
  references are rejected. `{}` removes all such references.
- If the URL's scheme, host or port changes, replace or remove all retained fixed
  header values and remove environment references. This prevents forwarding saved
  credentials to a different origin.

Respect the list's `canEdit` flag. Project-defined and stdio entries are not editable
through PUT. Editing an editable packaged entry creates a global override; it does
not alter the packaged definition. Prefer adding your own uniquely named connection.

## Read first, then register your service

Prepare once in the same Bash shell. These commands do not connect to the MCP service
until you deliberately submit a write or refresh. GET list is read-only.

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

Stop if the API is unavailable or `canAddServers` is not true. Check existing names
before adding one. The following registers **your already-running service**; replace
the example address, port and path with its actual endpoint first. It may immediately
initiate discovery, so use a service you trust. The example needs no authentication;
for a protected service supply its required headers using a securely prepared file.

```bash
vbot_mcp_curl -X POST "$VBOT_MCP_API_URL/servers?workingDir=$VBOT_WORKING_DIR" \
  -H 'Content-Type: application/json' \
  --data-binary '{"name":"edu-tools","type":"http","url":"http://192.168.127.2:18081/mcp","headers":{}}' |
  jq .
```

### Refresh and check discovery

Create, edit and toggle already schedule discovery. Use an explicit refresh after
recovering a service or changing its tool definitions; it can reconnect configured
services in this context, not just `edu-tools`.

```bash
vbot_mcp_curl -X POST "$VBOT_MCP_API_URL/servers/refresh?workingDir=$VBOT_WORKING_DIR" |
  jq .

vbot_mcp_curl --get "$VBOT_MCP_API_URL/servers" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" |
  jq '{catalogReady,catalogRevision,refreshPending,diagnostics,storageAvailable,loadError,
       servers:[.servers[] | select(.name == "edu-tools")]}'
```

While `refreshPending` is true, wait and read GET again with a bounded deadline;
do not repeatedly POST refresh. After it clears, require `catalogReady=true`, your
entry `enabled=true`, no entry `configError` or relevant discovery diagnostic, and the
expected `toolCount`. `storageAvailable` describes enabled-state storage;
`canAddServers` and per-entry `canEdit` describe configuration operations. A `loadError`
needs investigation before further writes. GET by itself does not start discovery.

Saving a definition does not prove connectivity or tool execution. After successful
discovery, start a new Agent Turn and request one harmless tool call; confirm its
actual result at the service. Tools are exposed as normalized names such as
`mcp__edu_tools__edu_echo`, while direct MCP `tools/call` uses the raw name `edu_echo`.
Existing sessions can pick up the refreshed tools on subsequent Turns; do not assume
an executing Turn or in-flight call changes immediately. A session tool selection
must also permit the tool. No device reboot is required.

### Edit without revealing saved credentials

Read a fresh config, build the complete edit body, and review it before PUT.
This example retains every existing header and environment reference and keeps the
URL unchanged; edit `edit.json` deliberately if you want different settings.

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

Read GET config again to confirm URL and header names, then check discovery and a
harmless call in a new Turn. Redacted readback is not a credential backup: keep your
original secrets securely outside the repository. Protect and remove any local edit
files containing newly entered credentials after use.

### Disable or re-enable your connection

```bash
vbot_mcp_curl -X PATCH "$VBOT_MCP_API_URL/servers/edu-tools?workingDir=$VBOT_WORKING_DIR" \
  -H 'Content-Type: application/json' --data-binary '{"enabled":false}' |
  jq .
```

Use `{"enabled":true}` to re-enable the same connection. Read the list and check the
settled discovery state afterward. Do not toggle unrelated services.

## Errors and recovery

| Result | Handling |
| --- | --- |
| `400 mcp_server_invalid_body` / `mcp_server_invalid_config` | Check required fields, URL, name, header rules and the create/edit distinction. Do not retry unchanged input. |
| `409 mcp_server_already_exists` | Name or normalized tool-prefix collision; inspect the list and choose a distinct name. POST does not replace an existing entry. |
| `409 mcp_server_config_changed` | Fetch a fresh config/revision, compare changes and rebuild the complete edit. |
| `404 mcp_server_not_found` | Refresh the list and confirm the exact name/context; do not infer that all APIs are unavailable. |
| `405 mcp_server_read_only` | Respect the source/transport and `canEdit`; add your own HTTP entry instead of modifying protected definitions. |
| `500 mcp_config_write_failed` / `mcp_server_state_write_failed`, or `503 mcp_config_unavailable` | Preserve the error and contact support; do not change device permissions or overwrite configuration files to bypass the API. |
| Non-2xx, timeout or interrupted write | Inspect status/body safely, then GET the list/config before deciding whether to retry: the write may already have persisted. Never blindly repeat POST/PUT. |
| Saved but no tools | Check `enabled`, refresh completion, `configError`, diagnostics, device-to-service networking, authentication, MCP transport and declared tools. A service with no tools cannot satisfy a tool-based request. |

Continue with the [tool contract](http-mcp.md) and
[integration guide](../../guides/agent-integration.md). Device Skills and `AGENTS.md`
are separate [content APIs](content-api.md), not MCP server definitions.
