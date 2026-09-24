# Call a read-only service

<p align="center">English | <a href="README.zh-CN.md">中文</a></p>

[Recipes index](../README.md) · [Python](main.py) · [C++](main.cc)

Interface: `/light_node/status` — service.

Generated types: `aorta.services.peripheral.GetLightStatusResponse`.

Reads whether the ear light is enabled, current mode, RGB and brightness. The request contains only the SDK-supplied header. It does not change the light. Status 0 means the query succeeded, not that a physical light effect was observed. Service calls select a single provider and disable automatic retries.

## Python: build and offline preview

```bash
bazel build //recipes/service-call:main
bazel run //recipes/service-call:main
```

By default, prints only a JSON request plan: no SDK installation, device connection, or request.

## Python: run on the robot

First complete [Python deployment](../../docs/development/python-deployment.md): transfer this recipe and matching wheels, then create the device venv. In the resulting application directory (APP_DIR), with its venv activated and device environment configured, run:

```bash
python -m recipes.service-call.main --execute --timeout 10
```



## C++

First follow the [C++ SDK guide](../../packages/aorta/cpp/README.md) for matching SDK/Schema archives, compiler and two artifact paths. On the build machine, build the C++ target explicitly; even previews require SDK linkage, but never create a Node or access a device:

```bash
bazel build //recipes/service-call:main_cpp
bazel run //recipes/service-call:main_cpp
```

Follow [binary deployment](../../packages/aorta/cpp/README.md#run-on-the-robot) with RECIPE=service-call. After vbot SSH login, switch to the deployed application directory and configure the shell and library path as shown there. With the task prerequisites above satisfied, run the executable directly:

```bash
./bin/service-call --execute --timeout 10
```

The robot does not need Bazel, a compiler, or a repository checkout. C++ uses the same routes, operation permissions and completion conditions as Python; read-only subscriptions never publish commands.

## Completion, failures and exit

Output is JSON Lines. Exit 0 means the example finished (including an offline preview), 1 runtime failure/timeout, 2 invalid arguments, and 130 interruption. Check the execute flag and output semantics; a preview is not live success. Waits are bounded; receive-queue overflow is an error rather than silently claiming complete data. Subscribers, clients and Node are closed on exit.

For tests, see [Recipes](../README.md); default tests never connect to or operate a robot.
