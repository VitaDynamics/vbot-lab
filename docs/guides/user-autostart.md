# Start user programs at boot

<p align="center">English | <a href="user-autostart.zh-CN.md">中文</a></p>

The system invokes `/userdata/vbot/init.sh` **as the vbot user during startup**.
Use this entry point to launch user programs automatically after the device reboots;
no interactive SSH session is required. This guide applies to the current
`foot_quadruped` EDU software.

This is a boot entry point, not a process supervisor. It does not by itself restart a
crashed application, rotate logs, or guarantee that network connections and robot interfaces
are ready. Applications must handle unavailable dependencies with bounded waits and clear
errors. Autostart does not grant additional permissions or change process resource limits.

## 1. Prepare the application

First [connect and log in](../robots/quadruped-common/connection.md) using the vbot account.
Run the following commands in the device's SSH shell, not the development container:

```bash
whoami
test -w /userdata/vbot
command -v bash
command -v python3
command -v nohup
command -v flock
```

Expect the account to be `vbot`; each check must succeed. If a command is missing, resolve
the missing dependency before continuing. Deploy an application and dependencies compatible
with the device's architecture and Python environment. The example below uses your own
foreground Python program at `/userdata/vbot/apps/my_app/main.py`; this file is not supplied
by VBOT Lab. Adjust the paths and interpreter for your application, including its virtual
environment if applicable. See the [development workflow](../development/README.md).

```bash
umask 077
mkdir -p /userdata/vbot/apps/my_app/logs /userdata/vbot/apps/my_app/run
test -r /userdata/vbot/apps/my_app/main.py
```

Stop if the application file is missing. Ensure it has a safe startup behavior and an
explicit stopping procedure before enabling autostart. Do not make robot movement an
unconditional consequence of booting the device.

## 2. Create an application launcher

Using a text editor, create `/userdata/vbot/apps/my_app/start.sh` with the following content.
Back up any existing file to an unused filename before editing it:

```bash
#!/bin/bash
umask 077

export PATH="/opt/vita/aorta/bin:$PATH"
export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5
source /opt/vita/ros/humble/setup.bash || exit 1
source /opt/vita/aorta/ros/local_setup.bash || exit 1
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=178
export ROS_LOCALHOST_ONLY=1

cd /userdata/vbot/apps/my_app || exit 1
exec 9>/userdata/vbot/apps/my_app/run/my_app.lock || exit 1
if ! flock -n 9; then
    printf '%s\n' 'Cannot acquire my_app lock; check for an existing instance.' >&2
    exit 1
fi
exec python3 -u /userdata/vbot/apps/my_app/main.py
```

The launcher explicitly loads the [device environment](../getting-started/device-environment.md):
boot processes must not rely on interactive `.bashrc` settings. If the application uses
neither Aorta nor ROS 2, omit that environment block; an Aorta-only application does not
need the ROS setup commands or DDS variables.

The nonblocking file lock prevents duplicate instances started through this launcher.
Keep the application in the foreground and retain file descriptor `9`; `exec` replaces the
launcher with the application, which holds the lock for its lifetime. Do not delete the lock
file to force a second instance: the file's existence does not mean its lock is held.
Directly starting the application without this launcher bypasses the lock.

```bash
chmod u+x /userdata/vbot/apps/my_app/start.sh
bash -n /userdata/vbot/apps/my_app/start.sh
```

After checking the application's operating preconditions, run the launcher once in the
foreground to check its dependencies and startup errors:

```bash
bash /userdata/vbot/apps/my_app/start.sh
```

Stop it using the application's stopping procedure (for example, Ctrl+C if supported), and
confirm that it and any child processes have exited before enabling boot startup.
This command runs the application; it is not a read-only environment check.

## 3. Register the boot entry

Inspect `/userdata/vbot/init.sh` before changing it. If it already exists, back it up to an
unused filename and **preserve its interpreter and other startup commands**. Add the marked
block below only once, before any unconditional exit. For a new file, use the complete
example, including the first line:

```sh
#!/bin/sh
# BEGIN my_app autostart
nohup /bin/bash /userdata/vbot/apps/my_app/start.sh </dev/null >>/userdata/vbot/apps/my_app/logs/startup.log 2>&1 &
# END my_app autostart
```

The trailing background operator lets the boot entry return promptly; `nohup` and the
redirections detach the application from terminal input and preserve its output in the log.
They do not provide crash recovery. Keep interactive prompts, foreground infinite loops,
and long dependency waits out of the boot entry itself.

For the new POSIX-shell entry shown above:

```bash
sh -n /userdata/vbot/init.sh && chmod u+x /userdata/vbot/init.sh
```

For an existing Bash entry, use `bash -n` instead and retain its original interpreter.
Do not add Bash-specific environment commands directly to a POSIX-shell entry; the Bash
launcher already handles them. Do not execute the entire existing boot entry just to test
one application, because it may start other user programs.

## 4. Confirm startup after reboot

When it is safe to restart the device and no other task is running, use the normal device
restart procedure. Reconnect over SSH and check the process **before manually launching it**:

```bash
whoami
pgrep -a -u vbot -f '/userdata/vbot/apps/my_app/main[.]py'
ps -u vbot -o pid,ppid,lstart,args
tail -n 50 /userdata/vbot/apps/my_app/logs/startup.log
```

For this long-running example, expect one application instance owned by vbot, and use the
application's own readiness signal to confirm startup. The boot entry returning successfully
does not prove that the background application initialized successfully. A short-lived
program may already have exited; use its own completion output instead of expecting a
persistent process. A log can be empty if the application emits no output; include startup
timestamps in your application's logs to distinguish the current boot from earlier runs.

## 5. Update, disable, and troubleshoot

- To disable this application's autostart, remove or comment out only its marked block in
  the boot entry. Preserve other applications' commands. This affects future launches and
  does not stop an already-running process.
- To stop the current instance, use the application's stopping procedure. If sending a
  termination signal manually, first confirm the current PID, owner, and command; do not
  kill every Python process. Wait for the application and its children to exit before
  replacing files or relaunching it. Keep a recoverable copy when updating the application.
- The example appends output to a persistent log. Configure bounded logging or rotation
  appropriate to the application so logs cannot fill the device's writable storage.
- If nothing starts, check the entry's filename, interpreter, executable/read permissions,
  syntax, and the existence of the application, log, and run directories. Use Unix line
  endings for shell scripts.
- If foreground startup works but boot startup fails, check absolute paths, the launcher's
  environment and interpreter, and dependency availability during boot. A fixed delay is
  not a substitute for checking a required service's readiness.
- If the lock cannot be acquired, check for an existing instance and directory permissions.
  If the application exits, inspect its error output; this entry point does not restart it.
