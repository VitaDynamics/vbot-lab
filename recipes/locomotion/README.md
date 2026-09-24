# Execute a body action

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

Interfaces: `/locomotion/set_run_mode`, `/locomotion/lowlevel_action`, `/locomotion/body/task_report`, `/locomotion/action_report`, `/locomotion/status` — service + pub/sub.

Generated types: `aorta.services.locomotion.SetRunModeRequest`, `aorta.services.locomotion.LowlevelActionRequest`, `aorta.topic.task.TaskReport`, `locomotion.ActionReport`, `locomotion.LocomotionStatus`.

Requires an authorized, supervised operation, a clear workspace, a known stopping procedure and no competing controller or task. The example first requires two different heartbeat sequences and an idle standing/lying posture. This conservative guard is not a safety interlock; `safe-stop` here is not an emergency-stop tool.

| Mode | Request |
| --- | --- |
| `stand` | `/locomotion/set_run_mode`: `MANUAL=0`, `target_state=1`, with an explicit `traction_user_param.is_user_param=false` |
| `lie-down` | `/locomotion/lowlevel_action`: `SAFE_LAYDOWN_SEQUENCE=4`, `target_state=1` |
| `safe-stop` | `/locomotion/lowlevel_action`: `SAFE_STOP_SEQUENCE=3`, `target_state=1` |

Standing and lying down use the core motion operations behind the device harness `pose` actions. They do not run the accompanying head, light, or sound behavior. `FIXED_STAND` and `FIXED_LAYDOWN` are different operations, not substitutes for these requests.

## Python: build and offline preview

```bash
bazel build //recipes/locomotion:main
bazel run //recipes/locomotion:main -- --mode stand
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.locomotion.main --mode stand --confirm-motion --execute --timeout 20
```

The report subscriber is opened **before** sending the request. A unique `req_id` is logged before submission. Status/error_code zero in the service response only means admission.

- `stand`: wait for the matching `/locomotion/body/task_report` with `LocomotionTaskResult.stage=EXECUTE` and successful status. This reports mode activation, not physical standing completion. Then observe three advancing status samples with standing posture, idle motion, and `current_action=RL_TROT`. Status has no request ID: the output explicitly labels this as observation, not causal completion. The controller continues running after the program exits.
- `lie-down` / `safe-stop`: wait for a BODY `/locomotion/action_report` with the same request ID, `terminal_status=SUCCESS` and `error_code=0`.

Confirm the actual posture and stability on site. On timeout, interruption, or lost response, the outcome may be unknown and the device may still be acting. Inspect state and use the established stopping procedure; exiting the program does not cancel motion. No blind retries or fallback commands are sent. The example does not publish velocity or joystick commands.

## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/locomotion:main_cpp
bazel run //recipes/locomotion:main_cpp -- --mode stand
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=locomotion. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/locomotion --mode stand --confirm-motion --execute --timeout 20
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
