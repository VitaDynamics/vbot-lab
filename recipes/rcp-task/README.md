# Submit an RCP DAG

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

For custom graphs and supplied behaviors, see [DAG authoring](../../docs/guides/rcp-dag.md)
and the [RCP presets](../../docs/guides/rcp-presets.md).

Interface: `/rcp/execute_task` — action.

Generated types: `aorta.action.rcp.ExecuteTaskGoal`, `aorta.services.rcp.DagSpec`, `aorta.services.rcp.DagNode`.

Submits two sequential Sleep nodes (second depends on first), with no motion commands. It still occupies the task executor: confirm there is no conflicting task first. `make_goal()` demonstrates the DagSpec union, NodeCommand.SleepCommand discriminator, NORMAL lifecycle and dependencies using generated object types, not an untyped JSON payload. Each Sleep is 1–10000 ms.

## Python: build and offline preview

```bash
bazel build //recipes/rcp-task:main
bazel run //recipes/rcp-task:main
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.rcp-task.main --execute --duration-ms 500 --timeout 10
```

A cancellable provider is required. Output includes `task_id`, `goal_id`, node progress and terminal status; it never prints the goal secret. Observe a terminal SUCCEEDED result with error_category=0, not only goal admission. To demonstrate cancellation of a longer non-motion DAG:

```bash
python -m recipes.rcp-task.main --execute --duration-ms 5000 --cancel-after 1 --timeout 15
```

A cancellation acknowledgement is not a terminal result. Natural completion can win the race; inspect the reported status. Timeout/interruption triggers a best-effort cancel and bounded terminal wait when a handle exists. An admission timeout can occur without a handle: use the logged identifiers to inspect the task; do not submit a duplicate DAG. Provider rejection or concurrent-task refusal is an error, not a reason to retry automatically.

## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/rcp-task:main_cpp
bazel run //recipes/rcp-task:main_cpp
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=rcp-task. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/rcp-task --execute --duration-ms 500 --timeout 10
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

[goal.h](goal.h) uses generated C++ `*Msg` types and variants for the same two Sleep nodes. The program logs feedback and terminal status. Cancellation example:

```bash
./bin/rcp-task --execute --duration-ms 5000 --cancel-after 1 --timeout 15
```

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
