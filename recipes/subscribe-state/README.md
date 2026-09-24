# Subscribe to state

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

Interface: `/locomotion/status` — pub/sub.

Generated types: `locomotion.LocomotionStatus`.

Prints heartbeat sequence, posture, motion, current action and timestamp. Posture: 0 unknown, 1 standing, 2 lying, 3 transitioning. Motion: 0 idle, 1 recovering, 2 emergency. This is read-only; a sample or changing heartbeat does not demonstrate motion completion. No samples before the deadline fails.

## Python: build and offline preview

```bash
bazel build //recipes/subscribe-state:main
bazel run //recipes/subscribe-state:main
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.subscribe-state.main --execute --count 3 --timeout 10
```



## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/subscribe-state:main_cpp
bazel run //recipes/subscribe-state:main_cpp
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=subscribe-state. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/subscribe-state --execute --count 3 --timeout 10
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
