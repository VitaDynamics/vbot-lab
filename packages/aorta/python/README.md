# Aorta Python SDK

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

The Aorta Python SDK is distributed as [vbot-lab release](https://github.com/VitaDynamics/vbot-lab/releases)
assets. SDK packages must currently be downloaded from GitHub Releases; cloning this
repository does not install them. Downloading requires network access, and installation
also needs access to PyPI for dependencies missing from the release. This page installs
the SDK, connects an EDU client to the robot, and receives live robot state. Check the
[compatibility matrix](../../../release/compatibility.md) for the supported robot software
image, and the release's `EDU_SDK_MANIFEST.json` for the version pairing.

Install the Python wheels from [edu-sdk-2026.9.24](https://github.com/VitaDynamics/vbot-lab/releases/tag/edu-sdk-2026.9.24)
(pre-release). The release manifest, not identical version numbers, defines the pairing:

| Distribution | Version | Purpose |
| --- | --- | --- |
| `aorta-sdk` | `2026.9.23` | `import aorta`; Python API and platform-specific native runtime |
| `aorta-msgs` | `2026.9.23` | Base generated messages and schema metadata |
| `vbot-edu-msgs` | `2026.9.24` | EDU generated messages and schema metadata |

The Aorta and EDU wheels carry their `LICENSE` and `NOTICE` under `.dist-info/licenses/`.
The FlatBuffers wheel from PyPI carries no license file, so the release attaches its upstream
license text as `flatbuffers-<ver>.LICENSE`.

Use Python 3.10 or newer. Published SDK wheel platforms are Linux x86_64, Linux aarch64,
and macOS arm64. Check the selected machine's architecture and native-library compatibility;
a workstation installation does not establish device firmware compatibility.
See [compatibility](../../../release/compatibility.md).

## 1. Choose the release wheels

From `edu-sdk-2026.9.24`, download these three wheels for the selected platform,
plus `SHA256SUMS` and `EDU_SDK_MANIFEST.json`:

| Wheel | Role |
| --- | --- |
| `aorta_sdk-<ver>-py3-none-<platform>.whl` | SDK package and native core for one platform |
| `aorta_msgs-<ver>-py3-none-any.whl` | Aorta message types |
| `vbot_edu_msgs-<ver>-py3-none-any.whl` | EDU message types and generated schema helpers |

Choose the `aorta_sdk` wheel for the machine — `linux_aarch64` (S100), `linux_x86_64`, or
`macosx_11_0_arm64`. Python 3.10 or newer is required. The `linux_*` tags are broad: those
two wheels are Ubuntu/glibc builds.

`vbot_edu_msgs` also needs `flatbuffers`. The release attaches the `flatbuffers` 25.12.19
wheel as well, so the four wheels install without network access; the commands below take
`flatbuffers==25.12.19` from PyPI instead. `EDU_SDK_MANIFEST.json` records every wheel
version under `pairing.wheels`.

## 2. Install with network access

Keep binaries out of Git. Put the three matching wheels, `SHA256SUMS`, and
`EDU_SDK_MANIFEST.json` in `artifacts/edu-sdk-2026.9.24/`. In the environment that
will run Python, ensure Python 3.10+, venv support, and access to PyPI are available.
From the parent of `artifacts/`, run on Linux:

```bash
uname -m
python3 --version
cd artifacts/edu-sdk-2026.9.24
sha256sum --ignore-missing -c SHA256SUMS
cd ../..
python3 -m venv .venv
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
SDK_PLATFORM=linux_x86_64
python -m pip install \
  "artifacts/edu-sdk-2026.9.24/aorta_sdk-2026.9.23-py3-none-${SDK_PLATFORM}.whl" \
  artifacts/edu-sdk-2026.9.24/aorta_msgs-2026.9.23-py3-none-any.whl \
  artifacts/edu-sdk-2026.9.24/vbot_edu_msgs-2026.9.24-py3-none-any.whl \
  "flatbuffers==25.12.19"
python -m pip check
python -c 'import aorta; from foxglove.CompressedVideo import CompressedVideo; from aorta.action.rcp.ExecuteTaskGoal import ExecuteTaskGoalT; print("SDK imports OK")'
```

Set `SDK_PLATFORM=linux_aarch64` **instead** on an ARM64 robot. For macOS arm64 use
`macosx_11_0_arm64` and an available SHA-256 verifier. Check that all three SDK wheel checksums
passed; missing files are ignored by the command above, not installed implicitly.
If Python, venv support, or native dependencies are unavailable, resolve that environment
first. Do not copy a workstation venv or x86_64 native libraries to the robot.

This command installs the three SDK packages from local Release downloads and fetches
FlatBuffers from PyPI. Do not add `--no-index` unless all required dependencies have
already been prepared locally. A failed download or missing dependency must be resolved
before continuing; cached packages are not evidence of a complete offline release.

For a robot without Internet access, follow [Python deployment](../../../docs/development/python-deployment.md):
first download the ARM64 SDK wheels and missing dependencies on a connected workstation,
then transfer the complete wheelhouse. Only the installation stage on that prepared
device can run offline; the initial download/preparation still requires a network.

Generated modules retain their Schema namespaces: for example `foxglove.CompressedVideo`,
`locomotion.LocomotionStatus`, and `aorta.services.*`.
The distribution name `vbot-edu-msgs` is **not** a Python import namespace.
Wheels include generated bindings and metadata; no local `flatc` generation is needed.

## 3. Connect

EDU programs connect to the robot's EDU router with the session files published in
`/opt/vita/aorta/edu/`:

| File | Use |
| --- | --- |
| `edu_session.json5` | Client mode. Suits the CLI, the Foxglove bridge and most programs |
| `edu_session_peer.json5` | Peer mode. Peers also exchange data directly with each other; the file reads `edu_dictionary.txt` |
| `edu_dictionary.txt` | Credential dictionary for peer mode |

Topic, service and action names are spelled with a leading slash (`/imu_raw`,
`/my_app/status`) and need no prefix. The session configuration adds the robot namespace on
the wire, so do not add it in the API call. Names in the robot's public interfaces reach the
robot as described in the [interface reference](../../../docs/interfaces/README.md); any
other name is shared only among EDU programs connected to the same robot, in client or peer
mode. EDU programs share one trust domain: another EDU program can publish under any name,
including a robot topic's name.

Use the node name `edu_sdk` or `edu_bridge` for programs that use robot interfaces: the
robot lists EDU nodes only under these names. The examples use `edu_sdk`. Other node names
work between EDU programs.

### On the robot (S100)

Run the client as `vbot` with a delivered session configuration, after loading the
[device shell environment](../../../docs/getting-started/device-environment.md):

```bash
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
```

Use `edu_session_peer.json5` instead for peer mode.

### From a workstation over X5 Wi-Fi

The X5 forwards TCP port 7447 on its Wi-Fi address to the EDU router. Copy a session
configuration from the robot into a private directory outside any project, keep its
`namespace` and credentials, and change only the `connect` endpoint. Replace
`<robot-alias>` with a name you choose for the robot:

```bash
dir="$HOME/.config/vbot/robots/<robot-alias>"
install -d -m 700 "$dir"
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_session.json5 "$dir/edu_session.json5"
chmod 600 "$dir/edu_session.json5"
perl -pi -e 's#tcp/127\.0\.0\.1:744[78]#tcp/<X5_WIFI_IP>:7447#g' "$dir/edu_session.json5"
nc -vz -w 3 <X5_WIFI_IP> 7447
export ZENOH_SESSION_CONFIG_URI="$dir/edu_session.json5"
```

For peer mode, also copy the dictionary and point `dictionary_file` at the local copy:

```bash
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_session_peer.json5 "$dir/edu_session_peer.json5"
scp vbot@<robot-address>:/opt/vita/aorta/edu/edu_dictionary.txt "$dir/edu_dictionary.txt"
chmod 600 "$dir/edu_session_peer.json5" "$dir/edu_dictionary.txt"
perl -pi -e 's#tcp/127\.0\.0\.1:7448#tcp/<X5_WIFI_IP>:7447#g' "$dir/edu_session_peer.json5"
perl -pi -e "s#/opt/vita/aorta/edu/edu_dictionary\.txt#$dir/edu_dictionary.txt#g" "$dir/edu_session_peer.json5"
export ZENOH_SESSION_CONFIG_URI="$dir/edu_session_peer.json5"
```

The session files and the dictionary carry the EDU credential. `chmod 600` only stops other
local users from reading them; it does not stop Git from committing a file inside a
repository. Keep the copies under `~/.config/vbot/robots/`, never in a project directory, and
do not paste them into issues or chat. This repository's `.gitignore` also ignores these file
names. Edit only the workstation copies; leave the files delivered on the device unchanged.

Robot software without the EDU router has no `edu_session_peer.json5`; its
`edu_session.json5` connects to port 7447 and supports client mode only, and names outside
the robot's public interfaces are dropped. The
[compatibility matrix](../../../release/compatibility.md) lists which software has the EDU
router.

## 4. Receive live state

Save this script as `subscribe_state.py` and run it with the environment from step 3. It
subscribes to `/imu_raw` and `/bms_state`, prints one line per stream, and exits after 20
samples of each:

```python
import threading
import time

import aorta
import aorta.topic.sensor.Imu as Imu
import bms.BmsState as BmsState

counts = {"imu": 0, "bms": 0}
first = {}
times = {}
done = threading.Event()


def update(name, field):
    now = time.monotonic()
    counts[name] += 1
    first.setdefault(name, field)
    times.setdefault(name, [now, now])[1] = now
    if all(count >= 20 for count in counts.values()):
        done.set()


def on_imu(message, _context):
    update("imu", (message.Seq(), message.FrameId()))


def on_bms(message, _context):
    update("bms", (message.VoltageMv(), message.SocPercent()))


with aorta.Node("edu_sdk") as node:
    node.create_subscriber_typed(
        lambda payload: Imu.Imu.GetRootAs(payload, 0), "/imu_raw", on_imu
    )
    node.create_subscriber_typed(
        lambda payload: BmsState.BmsState.GetRootAs(payload, 0),
        "/bms_state",
        on_bms,
    )
    if not done.wait(30):
        raise SystemExit(f"timeout counts={counts}")

for name in ("imu", "bms"):
    elapsed = times[name][1] - times[name][0]
    rate = (counts[name] - 1) / elapsed if elapsed else 0.0
    print(f"{name}: count={counts[name]} rate_hz={rate:.2f} first={first[name]!r}")
```

The first samples arrive immediately, and the script runs for roughly 20 seconds because
`/bms_state` publishes at about 1 Hz while `/imu_raw` publishes at about 104 Hz. Expected
output:

```text
imu: count=2069 rate_hz=104.01 first=(0, b'imu_link')
bms: count=20 rate_hz=1.00 first=(45750, 100.0)
```

Counts and first fields depend on the robot; the rates should stay near 104 Hz and 1 Hz.
A `SystemExit` with `timeout counts=...` means one stream stayed empty: check the session
configuration, the endpoint, and whether the selected robot software image serves the topic
in the [compatibility matrix](../../../release/compatibility.md).

## 5. Work without a robot

The SDK wheels contain no router, and the release does not ship one. For off-robot
development install the official Eclipse zenoh `zenohd` **1.10.x**, the zenoh minor the SDK
is built on, from its
[official release page](https://github.com/eclipse-zenoh/zenoh/releases) — for example
`zenoh-1.10.1-<arch>-<os>-standalone.zip`.

Start a local router, then point SDK nodes at it with the client configuration from the
Aorta quickstart:

```bash
zenohd --listen tcp/127.0.0.1:7447 --no-multicast-scouting
```

```bash
cat > /tmp/aorta_quickstart_client.json5 <<'EOF'
{
  mode: "client",
  connect: {
    endpoints: ["tcp/127.0.0.1:7447"]
  },
  scouting: {
    multicast: { enabled: false },
    gossip: { enabled: false }
  },
  transport: {
    shared_memory: { enabled: false }
  }
}
EOF
export ZENOH_SESSION_CONFIG_URI=/tmp/aorta_quickstart_client.json5
```

Check the installation with a local publish/subscribe round trip through that router:

```python
import threading

import aorta
import bms.BmsState as BmsState
import bms_state_schema_meta as schema

received = []
ready = threading.Event()


def decode(payload):
    return BmsState.BmsState.GetRootAs(payload, 0)


def on_message(message, _context):
    received.append((message.SensorTimestampNs(), message.VoltageMv()))
    ready.set()


with aorta.Node("edu_sdk") as node:
    node.create_subscriber_typed(decode, "/edu_verify/bms_state", on_message)
    publisher = node.create_publisher_typed(schema, "/edu_verify/bms_state")
    assert publisher.wait_for_matching(5000), "subscriber did not match"

    def fill(builder, header):
        BmsState.BmsStateStart(builder)
        BmsState.BmsStateAddAortaHeader(builder, header)
        BmsState.BmsStateAddSensorTimestampNs(builder, 987654321)
        BmsState.BmsStateAddVoltageMv(builder, 49500)
        return BmsState.BmsStateEnd(builder)

    publisher.publish_typed(fill)
    assert ready.wait(5), "message not received"
    assert received[-1] == (987654321, 49500), received
print("PUBSUB BMS OK", received[-1])
```

Expected output:

```text
PUBSUB BMS OK (987654321, 49500)
```

## Build, then run in the correct environment

Use the [offline build entry](../../../docs/development/offline-build.md) with a packaged
Bazel dependency bundle when building without registry access.
Image decoding and binary audio/video saving additionally use `numpy==2.2.6` for
bulk message-vector extraction; include its architecture-matching wheel in the wheelhouse.

From the workstation/container checkout root, Bazel 7.6.1 builds the Python entry points. A build does not
install wheels or package a cross-platform runtime. Select the interpreter containing
the matching wheel trio explicitly:

```bash
bazel build //recipes/...
PATH="$PWD/.venv/bin:$PATH" bazel run //recipes/subscribe-state:main -- --help
PATH="$PWD/.venv/bin:$PATH" bazel run //recipes/subscribe-state:main
```

Without `--execute`, every example prints an offline request plan and does not open
an Aorta session. SDK installation is unnecessary for those previews.
For live execution, follow [Python deployment](../../../docs/development/python-deployment.md):
build on the workstation, transfer the selected recipe and ARM64 wheelhouse, then create
and install a venv in a fresh device application directory. The robot has no preinstalled
checkout or application venv. After completing that guide, remain in its recorded APP_DIR
as `vbot` and run:

```bash
. .venv/bin/activate
unset PYTHONPATH
export PYTHONNOUSERSITE=1
export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```

The direct Python entry point works without Bazel installed on the robot; it runs the
same source as the Bazel target. The minimal deployment does not contain Bazel build
files; having Bazel installed alone does not make its targets available. These examples intentionally reject live
execution outside the device's `vbot` shell or with a different session configuration.
They do not guess a workstation router address. ROS 2 setup is not required for these
native Aorta examples.

Use a dedicated shell for these native SDK programs. ROS setup can add generated
Python packages to `PYTHONPATH` that take precedence over the venv (including another
`aorta-msgs` distribution). Activating a venv alone does not remove those paths.
The commands above isolate this shell from those packages; do not put the unset
command in your global shell startup file. Use a separate SSH shell for ROS tools.

## From Schema to SDK

Find fields, enum values, unions, and headers in [Schema](../../../schemas/README.md);
find route behavior and prerequisites in [interfaces](../../../docs/interfaces/README.md).
Use the generated accessors for received bytes. For typed service calls, pass the
matching `*_schema_meta` module and let the SDK supply the Aorta header.
For RCP, use generated object types with `FlatbuffersActionCodec`; the union
discriminator must match its payload. See the actual implementations in
[Recipes](../../../recipes/README.md).

A `Node` owns subscribers, clients, and action clients. Use context managers, bounded
queues and deadlines, and close resources on exit. A service acknowledgement is not
a completed motion; match its request identifier to a terminal report. An accepted
action cancellation is not yet a terminal canceled result. Timeouts can leave outcomes
unknown: inspect current state, rather than automatically repeating a write.

Offline tests never open a device session:

```bash
bazel test //tests:recipe_test
bazel test --test_env=PATH="$PWD/.venv/bin:$PATH" //tests:recipe_sdk_test
```

The second, explicit test requires the release wheels and checks generated-type
serialization without contacting a robot. See [Recipes](../../../recipes/README.md)
for camera, audio, motion, and RCP commands and their additional preconditions.

Single-task reference programs and complete applications are indexed in
[Recipes](../../../recipes/README.md) and [Blueprints](../../../blueprints/README.md).
