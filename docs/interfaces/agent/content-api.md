# Device Skill and AGENTS.md content API

<p align="center">English | <a href="content-api.zh-CN.md">中文</a></p>

Use these HTTP APIs to inject developer-authored content into the device's
`vbot-agent-harness`. They are not the installation mechanism for the Coding Agent
Skills in this repository's `skills/` directory. Read the [scope and compatibility](README.md)
and [authoring examples](customization.md) first.

## Connection and prerequisites

The agreed base URL is `http://192.168.127.10:8787`, reachable from the device's
development environment using the `vbot` account. The service is supplied with the EDU image;
confirm that the delivered version supports these routes before writing content.
No Harness source build, direct service-file access, or permission change is required.

This is HTTP JSON, not MCP: do not send JSON-RPC envelopes, initialize requests, or
`Mcp-Session-Id`. The MCP tool server at port `18080` is a different destination.
Use the service only on a trusted robot network in the single-trusted-developer scenario.
Do not expose or forward port `8787` to untrusted networks, campus public networks,
or the Internet. Instructions are not an OS permission or safety-policy mechanism.

Use UTF-8 JSON and `Content-Type: application/json` for writes. Successful responses
are HTTP `200` with the fields below, without a `data` wrapper.
`workingDir` is the service's agreed context selector, `/app/vbot-agent-harness`,
not your shell's current directory and not permission to write there.
The interface has no independent `/v1` version; compatibility follows the delivered image.

## Routes and data shapes

| Method and route | Query / JSON body | Success response |
| --- | --- | --- |
| `GET /api/skills` | Query `workingDir` | `{skills:[{name,description,source,path,shadowedByProject}]}` |
| `GET /api/skills/{name}` | Query `workingDir` | `{name:string,content:string,resources:string[]}` |
| `PUT /api/skills/{name}` | Body `{target:"user",content:string,workingDir?:string}` | `{path:string}` |
| `DELETE /api/skills/{name}` | Query `target=user` | `{deleted:true}` |
| `GET /api/agents-md` | Query `workingDir` | `{path:string,exists:boolean,content:string}` |
| `PUT /api/agents-md` | Body `{workingDir:string,content:string}`; non-empty `workingDir` | `{path:string}` |

Skill names use lowercase letters, digits, and hyphens. `content` is the entire
`SKILL.md`, including YAML frontmatter and a non-empty trigger `description`;
keep its `name` aligned with the route. EDU writes and deletes use `target=user` only.
PUT replaces `SKILL.md`, not a directory archive; arbitrary resource uploads are not supported.
DELETE removes the whole user Skill directory, including auxiliary files, not just `SKILL.md`.

In list entries, `name`, `description`, `source`, and `path` are strings;
`shadowedByProject` is boolean. The catalog can contain content from multiple layers.
Check the selected entry's source and precedence: a same-name entry may hide your user
Skill. The single-Skill GET returns resolved content, not a target-specific backup API.
Prefer a unique name; do not overwrite or delete a name whose ownership is unclear.

AGENTS.md PUT replaces the complete user-layer text atomically; it does not append.
GET `exists` can reflect compatibility fallback content, so it alone does not prove
a physical user file exists. GET is not the final combined system prompt.
There is no public AGENTS.md DELETE. Writing `""` clears user content; it does not
remove the file or remove the service's baseline instructions.

## Prepare and read before writing

The examples below are Bash commands using `curl` and `jq`, not a repository installer.
Run the preparation once in the same shell. All requests have timeouts and no automatic retries.
Override `VBOT_API_URL` only for a separately authorized or local test endpoint.

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

Review the catalog before using the example name `campus-guide`. If it is absent,
proceed to creation. If it already belongs to you and the resolved source is your
user content, back it up before replacement; otherwise choose a different name
consistently in the authoring file and every command below.

Run this block only for an existing Skill you have confirmed is yours:

```bash
vbot_curl --get "$VBOT_API_URL/api/skills/campus-guide" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_BACKUP_DIR/campus-guide-before.json"
jq . "$VBOT_BACKUP_DIR/campus-guide-before.json"
```

This JSON backup saves returned text and resource names, not auxiliary-file contents.
Retain the original resource bundle separately if one exists. Keep backups in your
own durable, private storage before deleting anything; a temporary directory is not
a long-term backup. Do not add personal content or backups to vbot-lab.

## Upload a device Skill and verify readback

In your own workspace, save and review the [Skill example](customization.md) as
`./campus-guide/SKILL.md`. The example opening hours are fictional.
The following command creates the Skill or replaces its complete entry-point text:

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

Expected output: the checked `{path:...}` response and `true` for content equality.
On an EDU-adapted image, the returned path must be under
`/userdata/.vbot/content/user/skills/`. An unexpected path is a failed adaptation check:
stop further writes and contact the platform team, without attempting direct filesystem repair.
The server may already have written content even if the path check fails.

## Back up, replace, and read AGENTS.md

Save and review the [instruction example](customization.md) as `./device-AGENTS.md`
in your own workspace. Do not upload vbot-lab's maintenance `AGENTS.md`.
First fetch the current API-visible content and review the backup:

```bash
vbot_curl --get "$VBOT_API_URL/api/agents-md" \
  --data-urlencode "workingDir=$VBOT_WORKING_DIR" \
  -o "$VBOT_BACKUP_DIR/agents-md-before.json"
jq . "$VBOT_BACKUP_DIR/agents-md-before.json"
```

After reviewing and keeping that backup, deliberately replace the user-layer text:

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

Expected output: the checked `{path:...}` response and `true`. The returned write path
must be `/userdata/.vbot/content/user/AGENTS.md`; treat any mismatch as an adaptation
failure, not permission to modify service files. Preserve your backup.

## Behavior validation, deletion, and recovery

Start a new Turn after each content change. For the Skill, ask a harmless question
that clearly matches its description and verify actual activation and use of its content.
A tool allowlist must retain the delivered service's Skill activation tool; do not use
an empty-tool session for this check. For AGENTS.md, observe the requested response
behavior. Saving / reading text does not prove either behavior, and already-running
Turns are not guaranteed to hot-reload. Neither kind of instruction enforces hard safety.

Deletion is optional and destructive. Only after confirming the Skill belongs to you
and separately backing up any auxiliary files, set `CONFIRM_SKILL_DELETE=campus-guide`
and run this block to remove that user Skill directory:

```bash
[[ "${CONFIRM_SKILL_DELETE:-}" == campus-guide ]]
vbot_curl -X DELETE "$VBOT_API_URL/api/skills/campus-guide?target=user" |
  jq -e '.deleted == true'
```

Re-list afterward: deletion of your user entry need not remove a same-name entry from
another layer. To restore saved text, review the backup's `content` and send it through
the corresponding PUT API again. This does not restore auxiliary files. For AGENTS.md,
PUT can restore API-visible text but cannot restore an originally absent physical file;
an empty write is not deletion. Validate restored behavior in a new Turn.

| Failure / risk | Required handling |
| --- | --- |
| Non-2xx / malformed response | Preserve HTTP status and safely inspect Content-Type and body; errors may be non-JSON |
| Missing Skill | The current documented implementation can return `500`, `extension_failed`, `retryable=false`; do not assume `404` or loop on all 5xx |
| `error.retryable` absent or false | Do not infer retry permission; retry read-only requests only for confirmed transient errors, with bounded backoff |
| PUT / DELETE timeout | Result is unknown; read the catalog / content before deciding what to do, never blindly resend |
| Concurrent edits | No ETag / If-Match concurrency guarantee; coordinate a single writer and avoid overwriting intervening changes |
| API unavailable on the delivered image | Confirm the supported version with the platform team; do not modify service configuration from the client |

Continue with the [integration guide](../../guides/agent-integration.md) to use the content
in a new Turn. Content updates do not require a device reboot or upgrade; do not change
system services or trigger robot motion as part of uploading content.
