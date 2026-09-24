"""Validate the public-facing scaffold without SDK, network, or device access."""

import argparse
import hashlib
import json
from xml.etree import ElementTree
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import unittest
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md",
    "LICENSE", "NOTICE",
    "MODULE.bazel", "MODULE.bazel.lock", "BUILD.bazel", ".bazelrc", ".bazelversion",
    "docs/README.md", "docs/overview/README.md", "docs/getting-started/README.md",
    "docs/hardware/README.md", "docs/hardware/sensors.md",
    "docs/hardware/quadruped-common/sensors.md", "docs/robots/README.md",
    "docs/robots/foot_quadruped/README.md", "docs/robots/wheel_quadruped/README.md",
    "docs/robots/quadruped-common/connection.md",
    "docs/robots/quadruped-common/assets/wired-connection.png",
    "docs/robots/foot_humanoid/README.md",
    "docs/development/README.md", "docs/interfaces/README.md", "docs/guides/README.md",
    "docs/interfaces/agent/README.md", "docs/interfaces/agent/http-mcp.md",
    "docs/interfaces/agent/customization.md", "docs/interfaces/agent/content-api.md",
    "docs/guides/agent-integration.md",
    "docs/guides/mapping-localization.md",
    "docs/guides/user-autostart.md",
    "docs/troubleshooting/README.md", "schemas/README.md",
    "packages/README.md", "packages/aorta/README.md", "packages/aorta/python/README.md",
    "recipes/README.md", "recipes/device-info/README.md",
    "recipes/subscribe-state/README.md", "recipes/service-call/README.md",
    "blueprints/README.md",
    "skills/README.md", "tools/README.md", "docker/README.md", "docker/compose.yaml",
    ".devcontainer/devcontainer.json", ".github/workflows/scaffold.yml",
    "tests/README.md", "release/README.md", "release/compatibility.md",
    "docs/agents/README.md", "catalog/README.md", "catalog/capabilities.json",
    "skills/vbot-dev-setup/SKILL.md", "tools/check_environment.py", "tools/vbot_catalog.py",
    "tests/test_agent_workspace.py", "tests/agent-scenarios/README.md",
    "docs/getting-started/device-environment.md", "docs/interfaces/aorta-ros2.md",
    "docs/interfaces/perception.md", "docs/interfaces/audio.md",
    "docs/interfaces/sensors.md", "docs/interfaces/cameras.md", "docs/interfaces/locomotion.md",
    "docs/interfaces/system-peripherals.md", "docs/interfaces/rcp.md",
    "tools/check_device_environment.py",
)


def tracked_files():
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "-z"], capture_output=True)
    if result.returncode == 0 and result.stdout:
        names = result.stdout.decode().split("\0")
        return [REPO_ROOT / name for name in names if name and (REPO_ROOT / name).is_file()]
    # Bazel runfiles are not a Git checkout; walk the declared tree instead.
    skipped = (".git", ".agents", ".claude", "artifacts", ".venv", "dist", "__pycache__")
    return sorted(
        path for path in REPO_ROOT.rglob("*")
        if path.is_file() and not any(
            part in skipped or part.startswith("bazel-") for part in path.relative_to(REPO_ROOT).parts
        )
    )


def tracked_text_files():
    files = []
    for path in tracked_files():
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def markdown_files():
    return sorted(
        path for path in REPO_ROOT.rglob("*.md")
        if not any(
            part in (".git", ".agents", ".claude", "artifacts", ".venv", "dist") or part.startswith("bazel-")
            for part in path.relative_to(REPO_ROOT).parts
        )
    )


def translation_path(path):
    if path.name.endswith(".zh-CN.md"):
        return path.with_name(path.name.removesuffix(".zh-CN.md") + ".md")
    return path.with_name(path.stem + ".zh-CN.md")


def language_navigation(path):
    target = translation_path(path)
    link = target.name
    # PR template links must also work after GitHub inserts them into a PR body.
    if path.name.startswith("pull_request_template."):
        link = "https://github.com/VitaDynamics/vbot-lab/blob/main/" + target.relative_to(REPO_ROOT).as_posix()
    if path.name.endswith(".zh-CN.md"):
        return f'<p align="center"><a href="{link}">English</a> | 中文</p>'
    return f'<p align="center">English | <a href="{link}">中文</a></p>'


def document_links(content):
    return (
        re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
        + re.findall(r'''(?:href|src)=["']([^"']+)["']''', content)
    )


class RepositoryChecks(unittest.TestCase):
    def test_viewer_guide_is_discoverable_and_separate_from_live_data(self):
        images = []
        for suffix in (".md", ".zh-CN.md"):
            guide = REPO_ROOT / f"docs/guides/vbot-viewer{suffix}"
            content = guide.read_text()
            links = document_links(content)
            self.assertIn("https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU", links)
            self.assertIn(f"foxglove{suffix}", links)
            self.assertIn(f"../community/README{suffix}", links)
            self.assertIn(f"../../assets/robots/foot_quadruped/README{suffix}", links)
            self.assertIn("URDF", content)
            self.assertIn("MJCF", content)
            self.assertIn("Ctrl+S", content)
            self.assertIn("Ctrl+Shift+S", content)
            image_paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content)
            self.assertEqual(image_paths, ["assets/vbot-viewer/overview.jpg"])
            images.append(image_paths)
            for origin in (f"README{suffix}", f"AGENTS{suffix}", f"docs/README{suffix}",
                           f"docs/guides/README{suffix}", f"docs/guides/foxglove{suffix}",
                           f"docs/getting-started/README{suffix}",
                           f"docs/robots/foot_quadruped/README{suffix}"):
                source = REPO_ROOT / origin
                targets = [(source.parent / link).resolve()
                           for link in document_links(source.read_text())
                           if not urlsplit(link).scheme]
                self.assertIn(guide.resolve(), targets, origin)
        self.assertEqual(images[0], images[1])
        self.assertTrue((REPO_ROOT / "docs/guides/assets/vbot-viewer/overview.jpg").is_file())

    def test_robot_models_bundle_foot_quadruped_urdf(self):
        root = REPO_ROOT / "assets/robots"
        self.assertEqual(sorted(p.name for p in root.iterdir() if p.is_dir()), ["foot_quadruped"])
        model = root / "foot_quadruped"
        metadata = json.loads((model / "model.json").read_text())
        self.assertEqual(metadata["format_version"], 1)
        self.assertEqual(metadata["robot_type"], model.name)
        self.assertEqual(metadata["model_id"], "VbotBaboEDU")
        self.assertEqual(metadata["availability"], "bundled")
        self.assertEqual(metadata["urdf"], "urdf/VbotBaboEDU.urdf")
        self.assertIsNone(metadata["model_license"])
        self.assertEqual(metadata["textures"], [])
        self.assertEqual(metadata["viewer_url"], "https://vbot-viewer.vitarobot.cc/?model=VbotBaboEDU")
        self.assertFalse((model / "vbot_babo_edu").exists())
        self.assertFalse((model / "textures").exists())
        self.assertTrue((model / metadata["urdf"]).is_file())
        self.assertEqual(sorted(metadata["meshes"]),
                         sorted(f"meshes/{p.name}" for p in (model / "meshes").iterdir()))
        referenced = set()
        for urdf in (model / "urdf").glob("*.urdf"):
            for mesh in ElementTree.parse(urdf).getroot().iter("mesh"):
                filename = mesh.get("filename")
                self.assertTrue(filename.startswith("package://VbotBaboEDU/meshes/"), filename)
                referenced.add(filename.removeprefix("package://VbotBaboEDU/"))
        self.assertEqual(referenced, set(metadata["meshes"]))
        for suffix in (".md", ".zh-CN.md"):
            self.assertIn("bundled", (model / f"README{suffix}").read_text())
            self.assertIn("model.json", document_links((model / f"README{suffix}").read_text()))
        self.assertIn("//assets/robots/foot_quadruped:repository_files", (REPO_ROOT / "BUILD.bazel").read_text())

    def test_community_entry_points_and_issue_chooser(self):
        urls = ["https://forum.vbot.cn/c/help/9", "https://forum.vbot.cn/c/skills-agent/8",
                "https://forum.vbot.cn/c/ideas/7"]
        chooser = (REPO_ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text()
        self.assertIn("blank_issues_enabled: true", chooser)
        self.assertEqual(re.findall(r"^\s+url:\s+(\S+)$", chooser, re.M), urls)
        for suffix in (".md", ".zh-CN.md"):
            guide = REPO_ROOT / f"docs/community/README{suffix}"
            content = guide.read_text()
            links = document_links(content)
            for url in urls + ["https://forum.vbot.cn/", "https://forum.vbot.cn/guidelines",
                               "https://github.com/VitaDynamics/vbot-lab/issues"]:
                self.assertIn(url, links)
            self.assertIn(f"../../SECURITY{suffix}", links)
            # The feedback template is translated prose, not an executable example.
            self.assertEqual(len(re.findall(r"^> - \*\*", content, re.M)), 9)
            for origin in (f"README{suffix}", f"AGENTS{suffix}", f"CONTRIBUTING{suffix}",
                           f"docs/README{suffix}", f"docs/troubleshooting/README{suffix}",
                           f"docs/guides/vbot-viewer{suffix}"):
                source = REPO_ROOT / origin
                targets = [(source.parent / link).resolve()
                           for link in document_links(source.read_text())
                           if not urlsplit(link).scheme]
                self.assertIn(guide.resolve(), targets, origin)

    def test_user_autostart_examples_and_navigation(self):
        for suffix in (".md", ".zh-CN.md"):
            guide = REPO_ROOT / f"docs/guides/user-autostart{suffix}"
            text = guide.read_text()
            blocks = re.findall(r"```(bash|sh)\n(.*?)```", text, re.DOTALL)
            self.assertTrue(blocks)
            for shell, block in blocks:
                result = subprocess.run([shell, "-n"], input=block, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotRegex(block, r"\b(?:sudo|reboot|shutdown|systemctl|pkill|killall)\b")
            launcher = next(block for _, block in blocks if block.startswith("#!/bin/bash\n"))
            self.assertIn("source /opt/vita/ros/humble/setup.bash || exit 1", launcher)
            self.assertIn("source /opt/vita/aorta/ros/local_setup.bash || exit 1", launcher)
            self.assertNotIn(".bashrc", launcher)
            self.assertIn("cd /userdata/vbot/apps/my_app || exit 1", launcher)
            self.assertIn("flock -n 9", launcher)
            self.assertIn("exec python3 -u /userdata/vbot/apps/my_app/main.py", launcher)
            # A failed environment load must stop before the device paths or application
            # are accessed. The stub makes this an entirely local, offline check.
            failure = subprocess.run(
                ["bash", "--noprofile", "--norc"],
                input="source() { return 1; }\n" + launcher,
                capture_output=True, text=True,
            )
            self.assertEqual(failure.returncode, 1)
            self.assertEqual(failure.stderr, "")
            entry = next(block for shell, block in blocks if shell == "sh")
            self.assertIn("nohup /bin/bash /userdata/vbot/apps/my_app/start.sh", entry)
            self.assertIn("</dev/null >>/userdata/vbot/apps/my_app/logs/startup.log 2>&1 &", entry)
            self.assertNotIn("source ", entry)
            for origin in (f"AGENTS{suffix}", f"catalog/README{suffix}",
                           f"docs/guides/README{suffix}", f"docs/development/README{suffix}",
                           f"docs/getting-started/device-environment{suffix}"):
                source = REPO_ROOT / origin
                targets = [(source.parent / link).resolve()
                           for link in document_links(source.read_text())]
                self.assertIn(guide.resolve(), targets, origin)

    def test_apache_license_and_notices(self):
        # Unmodified text from https://www.apache.org/licenses/LICENSE-2.0.txt.
        # Keep this check offline; project-specific attribution belongs in NOTICE.
        license_bytes = (REPO_ROOT / "LICENSE").read_bytes()
        self.assertEqual(
            hashlib.sha256(license_bytes).hexdigest(),
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        )
        notice = (REPO_ROOT / "NOTICE").read_text()
        self.assertIn("VBOT Lab", notice)
        self.assertIn("VitaDynamics", notice)
        self.assertIn("Apache License, Version 2.0", notice)
        for name in ("README.md", "README.zh-CN.md", "CONTRIBUTING.md", "CONTRIBUTING.zh-CN.md"):
            with self.subTest(document=name):
                text = (REPO_ROOT / name).read_text()
                self.assertIn("Apache-2.0", text)
                self.assertIn("LICENSE", document_links(text))
                self.assertIn("NOTICE", document_links(text))
                self.assertNotIn("an open-source license has not yet been provided", text)
                self.assertNotIn("尚未提供开源许可证", text)

    def test_usage_guides_do_not_embed_device_acceptance_reports(self):
        report_content = re.compile(
            r"^#{1,6}\s+[^\n]*(?:acceptance|verification results|验收|验证结论)"
            r"|peak-to-peak|峰峰值",
            re.IGNORECASE | re.MULTILINE,
        )
        for folder in ("docs/guides", "docs/interfaces"):
            for path in sorted((REPO_ROOT / folder).rglob("*.md")):
                with self.subTest(document=str(path.relative_to(REPO_ROOT))):
                    self.assertNotRegex(path.read_text(), report_content)

    def test_public_files_exclude_internal_details(self):
        forbidden = re.compile(
            r"https?://[^\s)>]*\.(?:feishu|larksuite)\.(?:cn|com)"
            r"|\b\d+\.\d+\.\d+-\d{12,14}\+git[0-9a-f]+\b"
            r"|\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"
            r"|(?:^|[\s\"'`(])/(?:host|Users)/[\w.-]+|/home/(?!vbot\b|runner\b|<)[\w.-]+"
            r"|claude\.ai/code|\bClaude-Session\b"
            r"|\b(?:vita|sz|sh|bj)-\d+(?:-[a-z0-9]+)?\b",
            re.IGNORECASE | re.MULTILINE,
        )
        # Private repository names; case-sensitive so constants such as ERROR_INTERNAL pass.
        internal_repository = re.compile(r"\b[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*[-_]internal\b")
        internal_notes = re.compile(r"验收|\bacceptance\b", re.IGNORECASE)
        for path in tracked_text_files():
            if path == Path(__file__).resolve():
                continue
            text = path.read_text()
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertNotRegex(text, forbidden)
                self.assertNotRegex(text, internal_repository)
                if path.suffix == ".md":
                    self.assertNotRegex(text, internal_notes)

    def test_no_credentials_are_tracked(self):
        credential_names = re.compile(
            r"(?:^|/)(?:edu_session[^/]*\.json5|[^/]*dictionary[^/]*\.txt|[^/]*\.(?:pem|key)"
            r"|id_(?:rsa|ed25519|ecdsa)(?:\.pub)?|\.env(?:\.[^/]+)?)$"
        )
        credential_values = re.compile(r"(?:\busrpwd\b|\bpassword\b)[\"']?\s*[:=]\s*[\"'][^\"'<$]+[\"']", re.IGNORECASE)
        for path in tracked_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            with self.subTest(file=relative):
                if relative != ".env.example":
                    self.assertNotRegex(relative, credential_names)
                if path.suffix != ".md" and path in tracked_text_files():
                    self.assertNotRegex(path.read_text(), credential_values)
        ignored = (REPO_ROOT / ".gitignore").read_text().splitlines()
        for pattern in ("edu_session*.json5", "*dictionary*.txt"):
            self.assertIn(pattern, ignored)

    def test_rcp_authoring_examples_and_resource_catalog(self):
        examples, catalogs = [], []
        for suffix in (".md", ".zh-CN.md"):
            guide = (REPO_ROOT / f"docs/guides/rcp-dag{suffix}").read_text()
            blocks = re.findall(r"```json\n(.*?)```", guide, re.S)
            self.assertEqual(len(blocks), 4)
            goals = [json.loads(block) for block in blocks]
            self.assertEqual([g["input_type"] for g in goals],
                             ["DagPresetRef", "DagPresetRef", "DagSpec", "DagSpec"])
            for arg in goals[1]["input"]["template_args"]:
                json.loads(arg["value_json"])
            goal = goals[2]
            self.assertEqual(goal["input_type"], "DagSpec")
            nodes = goal["input"]["nodes"]
            self.assertEqual([n["id"] for n in nodes], ["first", "second"])
            self.assertEqual(nodes[1]["dependencies"], ["first"])
            self.assertTrue(all(n["command_type"] == "SleepCommand" for n in nodes))
            examples.append(goals)
            catalog = (REPO_ROOT / f"docs/guides/rcp-presets{suffix}").read_text()
            presets = re.findall(r"^\| `([^`]+\.json)` \|", catalog, re.M)
            self.assertEqual(len(presets), 94)
            self.assertEqual(len(set(presets)), len(presets))
            self.assertTrue(all(not p.startswith("/") and ".." not in p for p in presets))
            expression_doc = (REPO_ROOT / f"docs/resources/expressions{suffix}").read_text()
            body_doc = (REPO_ROOT / f"docs/resources/body-trajectories{suffix}").read_text()
            emotions = re.findall(r"^\| (\d+) \| `(\d{3}_[^`]+)` \|", expression_doc, re.M)
            self.assertEqual(len(emotions), 116)
            self.assertEqual(len({int(row[0]) for row in emotions}), 116)
            for number, name in emotions:
                self.assertEqual(int(number), int(name[:3]))
            trajectories = re.findall(
                r"^\| `([^`]+\.npz)` \| `(RL_ACTION_POLICY[1-4])` \| ([^|]+) \| ([^|]+) \|$",
                body_doc, re.M,
            )
            self.assertEqual(len(trajectories), 71)
            self.assertEqual(len({row[0] for row in trajectories}), 71)
            body_pairs = []
            for resource, method, description, references in trajectories:
                self.assertNotIn("/", resource)
                self.assertTrue(description.strip())
                referenced_presets = re.findall(r"`([^`]+\.json)`", references)
                self.assertTrue(referenced_presets)
                self.assertTrue(set(referenced_presets).issubset(presets))
                body_pairs.append((resource, method, referenced_presets))
            self.assertIn(
                ("WAVE_50hz.npz", "RL_ACTION_POLICY1", ["actions/WAVE.json"]),
                body_pairs,
            )
            catalogs.append((presets, emotions, body_pairs))
            self.assertIn(f"rcp-presets{suffix}", document_links(guide))
            self.assertIn(f"rcp-dag{suffix}", document_links(catalog))
        self.assertEqual(examples[0], examples[1])
        self.assertEqual(catalogs[0], catalogs[1])

    def test_rcp_command_reference_covers_schema(self):
        schema = (REPO_ROOT / "schemas/aorta/schemas/service/rcp/function_input.fbs").read_text()
        types = re.search(r"union NodeCommand \{(.*?)\}", schema, re.S).group(1)
        names = re.findall(r"\b(\w+Command)\b", types)
        self.assertEqual(len(names), 13)
        for suffix in (".md", ".zh-CN.md"):
            reference = (REPO_ROOT / f"docs/interfaces/rcp-commands{suffix}").read_text()
            for name in names:
                section = reference.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0]
                table = re.search(r"table " + name + r" \{(.*?)\}", schema, re.S).group(1)
                fields = re.findall(r"^\s*(\w+):", table, re.M)
                documented = re.findall(r"^\| `(\w+)` \|", section, re.M)
                self.assertEqual(set(documented), set(fields), name)

    def test_head_trajectory_resources_and_pairings(self):
        variants = []
        for suffix in (".md", ".zh-CN.md"):
            page = (REPO_ROOT / f"docs/resources/head-trajectories{suffix}").read_text()
            body = (REPO_ROOT / f"docs/resources/body-trajectories{suffix}").read_text()
            presets_doc = (REPO_ROOT / f"docs/guides/rcp-presets{suffix}").read_text()
            body_names = set(re.findall(r"^\| `([^`]+\.npz)` \|", body, re.M))
            presets = set(re.findall(r"^\| `([^`]+\.json)` \|", presets_doc, re.M))
            rows = re.findall(
                r"^\| `([^`]+\.csv)` \| `(STREAM)` \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$",
                page, re.M,
            )
            self.assertEqual(len(rows), 66)
            self.assertEqual(len({row[0] for row in rows}), 66)
            mapped = {}
            for name, method, description, bodies, references in rows:
                self.assertNotIn("/", name)
                self.assertTrue(description.strip())
                linked_bodies = re.findall(r"`([^`]+\.npz)`", bodies)
                linked_presets = re.findall(r"`([^`]+\.json)`", references)
                self.assertTrue(linked_presets)
                self.assertTrue(set(linked_bodies).issubset(body_names))
                self.assertTrue(set(linked_presets).issubset(presets))
                mapped[name] = (method, linked_bodies, linked_presets)
            self.assertEqual(mapped["WAVE.csv"],
                             ("STREAM", ["WAVE_50hz.npz"], ["actions/WAVE.json"]))
            self.assertEqual(mapped["HAPPY_JUMP.csv"][1], ["HAPPY_BOUNCE_50hz.npz"])
            self.assertEqual(mapped["FORTUNE_CAT.csv"][1],
                             ["FORTUNE_CAT_50hz.npz", "FORTUNE_CAT_L_50hz.npz"])
            self.assertIn(f"head-trajectories{suffix}", document_links(body))
            variants.append(mapped)
        self.assertEqual(variants[0], variants[1])

    def test_foxglove_launch_commands_match_translations(self):
        variants = []
        for suffix in (".md", ".zh-CN.md"):
            page = (REPO_ROOT / f"docs/guides/foxglove{suffix}").read_text()
            scripts = re.findall(r"```bash\n(.*?)```", page, re.S)
            self.assertEqual(len(scripts), 3)
            variants.append(scripts)
            for script in scripts:
                result = subprocess.run(["bash", "-n"], input=script, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            published = scripts[1]
            for required in ("--config /opt/vita/aorta/edu/foxglove_bridge.yaml",
                             "--host 192.168.126.2", "--port 8765"):
                self.assertIn(required, published)
            self.assertNotIn("--include", published)
            launch = scripts[2]
            topics = re.findall(r"--include ([^\s\\]+)", launch)
            self.assertEqual(len(topics), 46)
            self.assertEqual(len(set(topics)), 46)
            self.assertTrue(all(not topic.startswith("/") for topic in topics))
            for required in ("--group default", "--host 192.168.126.2", "--port 8765",
                             "--zenoh-config /opt/vita/aorta/edu/edu_session.json5"):
                self.assertIn(required, launch)
            self.assertIn("export ZENOH_SESSION_CONFIG_URI=/opt/vita/aorta/edu/edu_session.json5", scripts[0])
            self.assertIn("ws://192.168.126.2:8765", page)
        self.assertEqual(variants[0], variants[1])

    def test_mapping_workflow_commands_match_and_use_json(self):
        documents = [(REPO_ROOT / f"docs/guides/mapping-localization{suffix}").read_text()
                     for suffix in (".md", ".zh-CN.md")]
        blocks = [re.findall(r"```bash\n(.*?)```", text, re.DOTALL) for text in documents]
        self.assertEqual(blocks[0], blocks[1])
        self.assertEqual(re.findall(r"`([^`\n]+)`", documents[0]),
                         re.findall(r"`([^`\n]+)`", documents[1]))
        requests = []
        for block in blocks[0]:
            result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for line in block.splitlines():
                args = shlex.split(line)
                self.assertEqual(args[0], "timeout")
                self.assertRegex(args[1], r"^[1-9][0-9]*s$")
                self.assertEqual(args[2], "aorta")
                self.assertNotIn("--once", args)
                if args[3:5] == ["service", "call"]:
                    self.assertEqual(args[5], "/slam/set_slam_mode")
                    self.assertEqual(args[7:], ["--timeout", "5"])
                    requests.append(json.loads(args[6]))
        self.assertEqual(requests, [
            {"mode": 1, "map_name": ""},
            {"mode": 2, "map_name": ""},
            {"mode": 2, "map_name": "edu_lab_1f"},
            {"mode": 3, "request_reloc": True, "map_name": "edu_lab_1f"},
            {"mode": 3, "request_reloc": True, "map_name": ""},
        ])

    def test_device_environment_shell_examples(self):
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/getting-started/device-environment{suffix}").read_text()
            blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
            for block in blocks:
                result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            setup = next(block for block in blocks if "# BEGIN VBOT EDU environment" in block)
            # Stub source: validate export order and values without loading device files.
            stub = '''source() {
  VBOT_TEST_SOURCES="${VBOT_TEST_SOURCES:+$VBOT_TEST_SOURCES,}$1"
  export RMW_IMPLEMENTATION=wrong ROS_DOMAIN_ID=wrong ROS_LOCALHOST_ONLY=wrong
}
'''
            observed = '''printf '%s\\n' "$PATH" "$ZENOH_SESSION_CONFIG_URI" "$VBOT_TEST_SOURCES" "$RMW_IMPLEMENTATION" "$ROS_DOMAIN_ID" "$ROS_LOCALHOST_ONLY"'''
            result = subprocess.run(["bash", "--noprofile", "--norc", "-c", stub + setup + observed],
                                    env={"PATH": "/usr/bin"}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                "/opt/vita/aorta/bin:/usr/bin", "/opt/vita/aorta/edu/edu_session.json5",
                "/opt/vita/ros/humble/setup.bash,/opt/vita/aorta/ros/local_setup.bash",
                "rmw_fastrtps_cpp", "178", "1",
            ])
            live_commands = [line for block in blocks for line in block.splitlines() if line.startswith("timeout ")]
            self.assertTrue(live_commands)
            for line in live_commands:
                self.assertRegex(line, r"^timeout 15s (aorta|ros2) (topic (list|echo)|service list|schema get|interface show)(?: |$)")
                if " topic echo " in line:
                    self.assertTrue("--count 1" in line or "--once" in line)
                if "ros2 topic" in line or "ros2 service" in line:
                    self.assertIn("--no-daemon", line)

    def test_aorta_ros2_reference_identifiers_match_translations(self):
        documents = [(REPO_ROOT / f"docs/interfaces/aorta-ros2{suffix}").read_text()
                     for suffix in (".md", ".zh-CN.md")]
        # Fenced commands are compared separately; their delimiters are not inline code.
        prose = [re.sub(r"```.*?```", "", text, flags=re.DOTALL) for text in documents]
        self.assertEqual(re.findall(r"`([^`\n]+)`", prose[0]), re.findall(r"`([^`\n]+)`", prose[1]))
        self.assertEqual(re.findall(r"```bash\n(.*?)```", documents[0], re.DOTALL),
                         re.findall(r"```bash\n(.*?)```", documents[1], re.DOTALL))

    def test_public_topic_inventory_and_safe_discovery_commands(self):
        command_topics = {"/locomotion/joy", "/locomotion/velocity_command", "/light/ear_modulation"}
        for suffix, subscribe, publish in ((".md", "subscribe", "publish"), (".zh-CN.md", "订阅", "发布")):
            text = (REPO_ROOT / f"docs/interfaces/aorta-ros2{suffix}").read_text()
            rows = [line.split("|")[1:-1] for line in text.splitlines()
                    if line.startswith("|") and "| pub/sub — " in line]
            self.assertEqual(len(rows), 46)
            topics = {row[1].strip(" `") for row in rows}
            self.assertEqual(len(topics), 46)
            for row in rows:
                self.assertEqual(len(row), 6)
                topic = row[1].strip(" `")
                self.assertEqual(row[3].strip(), f"pub/sub — {publish if topic in command_topics else subscribe}")
                self.assertIn("`", row[4])
                self.assertIn("/msg/", row[5])
            self.assertIn("| `/system/sm_status` | `/sm/status` |", text)
            self.assertIn("| `/slam/static_transforms` | `/tf_static` |", text)
            self.assertIn("| `/locomotion/joy` | `/joy` |", text)
            self.assertNotIn("/rcp/execute_task", topics)
            self.assertIn("`aorta_msgs/action/ExecuteTask`", text)
            self.assertNotIn("blocked_dependency", text)
            self.assertNotIn("No native EDU counterpart", text)
            self.assertNotIn("无原生 EDU 对应接口", text)
            for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
                result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for line in block.splitlines():
                    self.assertRegex(line, r"^timeout 15s (aorta|ros2) (topic echo|action (list|info)|interface show)(?: |$)")
                    if " topic echo " in line:
                        self.assertTrue("--count 1" in line or "--once" in line)
                        self.assertNotIn(shlex.split(line)[5], command_topics)
                    if "ros2 topic echo /tf_static" in line:
                        self.assertIn("--qos-durability transient_local", line)
                        self.assertIn("--qos-reliability reliable", line)

    def test_every_public_topic_links_to_a_family_usage_guide(self):
        expected = {
            "sensors": 12, "cameras": 10, "perception": 2, "audio": 5,
            "locomotion": 9, "system-peripherals": 3, "rcp": 1, "mapping-localization": 4,
        }
        for suffix in (".md", ".zh-CN.md"):
            source = REPO_ROOT / f"docs/interfaces/aorta-ros2{suffix}"
            counts = {}
            for line in source.read_text().splitlines():
                if not line.startswith("|") or "| pub/sub — " not in line:
                    continue
                cells = line.split("|")[1:-1]
                topic = cells[1].strip(" `")
                links = document_links(cells[0])
                self.assertEqual(len(links), 1, topic)
                target = (source.parent / links[0]).resolve()
                name = target.name.removesuffix(suffix)
                counts[name] = counts.get(name, 0) + 1
                self.assertTrue(target.is_file(), target)
                self.assertIn(f"`{topic}`", target.read_text(), f"{topic}: {target}")
            self.assertEqual(counts, expected)

    def test_family_guides_have_matching_identifiers_and_read_only_examples(self):
        for name in ("sensors", "cameras", "locomotion", "system-peripherals", "rcp"):
            documents = [(REPO_ROOT / f"docs/interfaces/{name}{suffix}").read_text()
                         for suffix in (".md", ".zh-CN.md")]
            with self.subTest(family=name):
                prose = [re.sub(r"```.*?```", "", text, flags=re.DOTALL) for text in documents]
                self.assertEqual(re.findall(r"`([^`\n]+)`", prose[0]),
                                 re.findall(r"`([^`\n]+)`", prose[1]))
                blocks = [re.findall(r"```bash\n(.*?)```", text, re.DOTALL) for text in documents]
                self.assertEqual(blocks[0], blocks[1])
                self.assertTrue(blocks[0])
                for block in blocks[0]:
                    result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    for line in block.splitlines():
                        self.assertRegex(line, r"^timeout 15s (aorta|ros2) (topic (list|echo)|schema get|action (list|info)|interface show)(?: |$)")
                        if " topic echo " in line:
                            self.assertTrue("--count 1" in line or "--once" in line)
                            self.assertNotIn(shlex.split(line)[5], {
                                "/locomotion/joy", "/locomotion/velocity_command", "/light/ear_modulation",
                            })

    def test_perception_and_audio_contracts_match_translations(self):
        contracts = {
            "perception": (
                ("/perception/detections2d", "perception.Detection2DArray", "vision_msgs/msg/Detection2DArray"),
                ("/perception/poses", "perception.PoseDetection", "vision_msgs/msg/PoseDetection"),
            ),
            "audio": (
                ("/raw_audio_dump", "foxglove.RawAudio", "foxglove_msgs/msg/RawAudio"),
                ("/audio/uwb_adpcm_segment", "foxglove.RawAudio", "foxglove_msgs/msg/RawAudio"),
                ("/uwb/audio_done", "aorta.uwb.AudioDoneEvent", "aorta_msgs/msg/AudioDoneEvent"),
                ("/speech/asr_result", "aorta.topic.speech.AsrResult", "aorta_msgs/msg/AsrResult"),
                ("/voice/event", "aorta.voice.VoiceEvent", "aorta_msgs/msg/VoiceEvent"),
            ),
        }
        for name, routes in contracts.items():
            documents = [(REPO_ROOT / f"docs/interfaces/{name}{suffix}").read_text()
                         for suffix in (".md", ".zh-CN.md")]
            with self.subTest(document=name):
                self.assertEqual(re.findall(r"`([^`\n]+)`", documents[0]),
                                 re.findall(r"`([^`\n]+)`", documents[1]))
                blocks = [re.findall(r"```bash\n(.*?)```", text, re.DOTALL) for text in documents]
                self.assertEqual(blocks[0], blocks[1])
                for text in documents:
                    self.assertIn("pub/sub", text)
                    for topic, aorta_type, ros_type in routes:
                        self.assertIn(f"| `{topic}` | `{aorta_type}` | `{topic}` | `{ros_type}` |", text)
                for block in blocks[0]:
                    result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    for line in block.splitlines():
                        self.assertRegex(line, r"^timeout 15s (aorta|ros2) (topic (list|echo)|schema get|interface show)(?: |$)")
                        if " topic echo " in line:
                            self.assertTrue("--count 1" in line or "--once" in line)
                        if "ros2 topic" in line:
                            self.assertIn("--no-daemon", line)
                        self.assertNotIn("topic echo /audio/uwb_adpcm_segment", line)
        for suffix in (".md", ".zh-CN.md"):
            index = (REPO_ROOT / f"docs/interfaces/aorta-ros2{suffix}").read_text()
            for routes in contracts.values():
                for topic, _, _ in routes:
                    self.assertIn(f"| `{topic}` | `{topic}` | pub/sub", index)

    def test_audio_sources_and_asr_provider_routing(self):
        expected = [
            ("BODY", "1", "`/raw_audio_dump`"),
            ("TAG", "2", "`/audio/uwb_adpcm_segment`"),
            ("UNKNOWN", "0", "—"),
        ]
        for suffix, sources in (
            (".md", ("Robot-body microphone", "UWB signalling", "Unspecified source")),
            (".zh-CN.md", ("本体麦克风", "UWB 信令", "来源未指定")),
        ):
            with self.subTest(language=suffix):
                text = (REPO_ROOT / f"docs/interfaces/audio{suffix}").read_text()
                rows = re.findall(
                    r"^\| `(BODY|TAG|UNKNOWN)` \| `(\d+)` \| ([^|]+) \| ([^|]+) \|$",
                    text, re.MULTILINE,
                )
                self.assertEqual([(name, value, topic.strip())
                                  for name, value, _, topic in rows], expected)
                for row, source in zip(rows, sources):
                    self.assertIn(source, row[2])
                self.assertIn("ros2 interface show aorta_msgs/msg/AsrResult", text)

    def test_device_entry_orders_login_before_shell_setup(self):
        for suffix in (".md", ".zh-CN.md"):
            guide = (REPO_ROOT / f"docs/robots/foot_quadruped/README{suffix}").read_text()
            links = document_links(guide)
            login = f"../quadruped-common/connection{suffix}"
            setup = f"../../getting-started/device-environment{suffix}"
            self.assertLess(links.index(login), links.index(setup))

    def test_agent_content_api_routes(self):
        expected = [
            "GET /api/skills", "GET /api/skills/{name}",
            "PUT /api/skills/{name}", "DELETE /api/skills/{name}",
            "GET /api/agents-md", "PUT /api/agents-md",
        ]
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/interfaces/agent/content-api{suffix}").read_text()
            routes = re.findall(r"^\| `((?:GET|PUT|DELETE) /api/[^`]+)` \|", text, re.MULTILINE)
            self.assertEqual(routes, expected)
            self.assertIn('target:"user"', text)
            self.assertNotIn('target:"project"', text)
            self.assertNotIn("DELETE /api/agents-md", text)

    def test_agent_content_api_documented_requests(self):
        expected = [
            ("--get", "/skills"), ("--get", "/skills/campus-guide"),
            ("-X PUT", "/skills/campus-guide"), ("--get", "/skills/campus-guide"),
            ("--get", "/agents-md"), ("-X PUT", "/agents-md"),
            ("--get", "/agents-md"), ("-X DELETE", "/skills/campus-guide?target=user"),
        ]
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/interfaces/agent/content-api{suffix}").read_text()
            blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
            self.assertEqual(len(blocks), 6)
            commands = "\n".join(blocks)
            self.assertEqual(
                re.findall(r'vbot_curl (--get|-X PUT|-X DELETE) "\$VBOT_API_URL/api([^\"]+)"', commands),
                expected,
            )
            self.assertIn('--rawfile content ./campus-guide/SKILL.md', commands)
            self.assertIn('--rawfile content ./device-AGENTS.md', commands)
            self.assertIn('select(.path == "/userdata/.vbot/content/user/skills/campus-guide/SKILL.md")', commands)
            self.assertIn('select(.path == "/userdata/.vbot/content/user/AGENTS.md")', commands)
            self.assertIn('[[ "${CONFIRM_SKILL_DELETE:-}" == campus-guide ]]', blocks[-1])

    def test_agent_content_api_shell_syntax(self):
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/interfaces/agent/content-api{suffix}").read_text()
            for index, block in enumerate(re.findall(r"```bash\n(.*?)```", text, re.DOTALL)):
                with self.subTest(language=suffix, block=index):
                    result = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_agent_mcp_json_examples(self):
        for suffix in (".md", ".zh-CN.md"):
            path = REPO_ROOT / f"docs/interfaces/agent/http-mcp{suffix}"
            examples = re.findall(r"```json\n(.*?)```", path.read_text(), re.DOTALL)
            self.assertEqual(len(examples), 3)
            definition, request, response = [json.loads(example) for example in examples]
            self.assertEqual(definition["name"], "edu_add")
            self.assertEqual(request["params"]["name"], definition["name"])
            self.assertEqual(request["method"], "tools/call")
            self.assertEqual(request["id"], response["id"])
            self.assertFalse(response["result"]["isError"])
            self.assertEqual(json.loads(response["result"]["content"][0]["text"])["value"], 3)

    def test_agent_mcp_documented_sequence(self):
        for suffix in (".md", ".zh-CN.md"):
            path = REPO_ROOT / f"docs/guides/agent-integration{suffix}"
            examples = re.findall(r"```bash\n(.*?)```", path.read_text(), re.DOTALL)
            self.assertEqual(len(examples), 1)
            requests = [json.loads(body) for body in re.findall(r"-d '([^']+)'", examples[0])]
            self.assertEqual(
                [request["method"] for request in requests],
                ["initialize", "notifications/initialized", "tools/list", "tools/call", "tools/call"],
            )
            self.assertEqual(requests[0]["params"]["protocolVersion"], "2025-06-18")
            self.assertNotIn("id", requests[1])
            self.assertEqual([request["params"]["name"] for request in requests[3:]], ["edu_echo", "edu_add"])

    def test_robot_type_documentation_entries(self):
        robot_types = ("foot_quadruped", "wheel_quadruped", "foot_humanoid")
        for suffix in (".md", ".zh-CN.md"):
            index = REPO_ROOT / f"docs/robots/README{suffix}"
            index_links = document_links(index.read_text())
            for robot_type in robot_types:
                with self.subTest(robot_type=robot_type, language=suffix):
                    guide_link = f"{robot_type}/README{suffix}"
                    self.assertIn(guide_link, index_links)
                    self.assertIn(f"`{robot_type}`", (index.parent / guide_link).read_text())

    def test_robot_dog_shared_connection_guide(self):
        for suffix in (".md", ".zh-CN.md"):
            with self.subTest(language=suffix):
                guide = REPO_ROOT / f"docs/robots/quadruped-common/connection{suffix}"
                text = guide.read_text()
                images = re.findall(r'''<img\b[^>]*\bsrc=["']([^"']+)["']''', text)
                self.assertEqual(images, ["assets/wired-connection.png"])
                self.assertIn(images[0], document_links(text))
                self.assertTrue((guide.parent / images[0]).is_file())
                for label in ("USB-C", "Ethernet Adapter", "Ethernet Port", "Developer Computer"):
                    self.assertIn(f"**{label}**", text)
                for value in (
                    "`foot_quadruped`", "`wheel_quadruped`", "`192.168.126.100`", "`192.168.126.2`",
                    "`255.255.255.0`", "`192.168.126.0/24`",
                ):
                    self.assertIn(value, text)
                blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
                self.assertEqual(len(blocks), 8)
                self.assertEqual(
                    [block.strip() for block in blocks[:4]],
                    ["ssh vbot@192.168.126.2", "whoami", "passwd", "exit"],
                )
                for page, link in (
                    ("docs/robots/foot_quadruped/README", f"../quadruped-common/connection{suffix}"),
                    ("docs/robots/wheel_quadruped/README", f"../quadruped-common/connection{suffix}"),
                    ("docs/robots/README", f"quadruped-common/connection{suffix}"),
                    ("docs/getting-started/README", f"../robots/quadruped-common/connection{suffix}"),
                    ("docs/development/README", f"../robots/quadruped-common/connection{suffix}"),
                ):
                    self.assertIn(link, document_links((REPO_ROOT / f"{page}{suffix}").read_text()))
                for robot_type in ("foot_quadruped", "wheel_quadruped"):
                    self.assertIn(f"../{robot_type}/README{suffix}", document_links(text))
                    self.assertFalse((REPO_ROOT / f"docs/robots/{robot_type}/connection{suffix}").exists())

    def test_public_key_setup_commands(self):
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/robots/quadruped-common/connection{suffix}").read_text()
            blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
            for block in blocks:
                result = subprocess.run(["bash", "-n"], input=block, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            # Parse only: never generate a key, access an agent or install anything.
            commands = [shlex.split(block.replace("\\\n", "")) for block in blocks]
            self.assertEqual([args for args in commands if args[0] == "ssh-keygen"], [[
                "ssh-keygen", "-t", "ed25519", "-f", "~/.ssh/id_ed25519", "-C", "vbot-dev",
            ]])
            self.assertEqual([args for args in commands if args[0] == "ssh-add"], [[
                "ssh-add", "~/.ssh/id_ed25519",
            ]])
            self.assertEqual([args for args in commands if args[0] == "ssh-copy-id"], [[
                "ssh-copy-id", "-i", "~/.ssh/id_ed25519.pub", "vbot@192.168.126.2",
            ]])

    def test_public_key_login_check_disables_password_fallback(self):
        # Only shell builtins run. Never contact a robot or read the real private key.
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        stub = '''timeout() {
  printf '%s\\n' "$1"
  shift
  "$@"
}
ssh() {
  printf '%s\\n' "$@"
  return "$VBOT_TEST_SSH_STATUS"
}
'''
        expected_options = [
            "-o", "BatchMode=yes", "-o", "PreferredAuthentications=publickey",
            "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ControlPath=none", "-o", "ConnectTimeout=5", "-o", "ConnectionAttempts=1",
            "vbot@192.168.126.2", "whoami",
        ]
        for suffix in (".md", ".zh-CN.md"):
            text = (REPO_ROOT / f"docs/robots/quadruped-common/connection{suffix}").read_text()
            blocks = re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
            probes = [block for block in blocks if "BatchMode=yes" in block]
            self.assertEqual(len(probes), 1)
            for status in (0, 255):
                with self.subTest(language=suffix, status=status):
                    result = subprocess.run(
                        [bash, "--noprofile", "--norc", "-c", stub + probes[0]],
                        env={"PATH": "", "VBOT_TEST_SSH_STATUS": str(status)},
                        capture_output=True, text=True, timeout=5,
                    )
                    self.assertEqual(result.returncode, status, result.stderr)
                    arguments = result.stdout.splitlines()
                    self.assertEqual(arguments[:2], ["10s", "-i"])
                    self.assertTrue(arguments[2].endswith("/.ssh/id_ed25519"))
                    self.assertEqual(arguments[3:], expected_options)

    def test_robot_dog_guides_share_sensor_specification(self):
        for suffix in (".md", ".zh-CN.md"):
            specification = REPO_ROOT / f"docs/hardware/quadruped-common/sensors{suffix}"
            self.assertTrue(specification.is_file())
            sensor_index = REPO_ROOT / f"docs/hardware/sensors{suffix}"
            self.assertIn(f"quadruped-common/sensors{suffix}", document_links(sensor_index.read_text()))
            for robot_type in ("foot_quadruped", "wheel_quadruped"):
                with self.subTest(robot_type=robot_type, language=suffix):
                    guide = REPO_ROOT / f"docs/robots/{robot_type}/README{suffix}"
                    self.assertIn(
                        f"../../hardware/quadruped-common/sensors{suffix}",
                        document_links(guide.read_text()),
                    )
            # The bipedal guide must not direct developers to robot-dog parameters.
            bipedal = REPO_ROOT / f"docs/robots/foot_humanoid/README{suffix}"
            self.assertFalse(any("quadruped-common/" in link for link in document_links(bipedal.read_text())))

    def test_sensor_specification_numeric_parity(self):
        english = (REPO_ROOT / "docs/hardware/quadruped-common/sensors.md").read_text()
        chinese = (REPO_ROOT / "docs/hardware/quadruped-common/sensors.zh-CN.md").read_text()
        # Keep signs, decimal values, and ordering aligned between translations.
        pattern = r"(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?"
        self.assertEqual(
            re.findall(pattern, english.replace("−", "-")),
            re.findall(pattern, chinese.replace("−", "-")),
        )

    def test_bilingual_document_pairs(self):
        for path in markdown_files():
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertTrue(translation_path(path).is_file(), "Missing translation")
                body = re.sub(r"\A---\n.*?\n---\n", "", path.read_text(), count=1, flags=re.DOTALL).lstrip()
                self.assertIn(language_navigation(path), body.splitlines()[:5])

    def test_translated_code_examples_match(self):
        for path in markdown_files():
            if path.name.endswith(".zh-CN.md"):
                continue
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                counterpart = translation_path(path)
                self.assertTrue(counterpart.is_file(), "Missing translation")
                self.assertEqual(
                    re.findall(r"```[^\n]*\n(.*?)```", path.read_text(), re.DOTALL),
                    re.findall(r"```[^\n]*\n(.*?)```", counterpart.read_text(), re.DOTALL),
                    "Keep commands and executable examples identical in both languages",
                )

    def test_document_links_keep_selected_language(self):
        for path in markdown_files():
            body = path.read_text().replace(language_navigation(path), "")
            for destination in document_links(body):
                target = urlsplit(destination.strip("<>"))
                if target.scheme or target.netloc or not target.path.endswith(".md"):
                    continue
                with self.subTest(file=str(path.relative_to(REPO_ROOT)), link=destination):
                    self.assertEqual(
                        path.name.endswith(".zh-CN.md"),
                        target.path.endswith(".zh-CN.md"),
                        "Document links must retain the selected language",
                    )

    def test_homepage_uses_root_readme(self):
        self.assertTrue((REPO_ROOT / "README.md").is_file())
        # GitHub prefers a .github README over the repository-root README.
        higher_priority_readmes = [
            path.name for path in (REPO_ROOT / ".github").iterdir()
            if path.is_file() and (
                path.name.casefold() == "readme"
                or path.name.casefold().startswith("readme.")
            )
        ]
        self.assertEqual(higher_priority_readmes, [], "Keep the homepage README at the repository root")

    def test_required_files(self):
        for relative in REQUIRED_FILES:
            with self.subTest(path=relative):
                self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_markdown_links(self):
        for path in markdown_files():
            relative = path.relative_to(REPO_ROOT)
            for destination in document_links(path.read_text()):
                target = urlsplit(destination.strip("<>"))
                if target.scheme or target.netloc or not target.path:
                    continue
                with self.subTest(file=str(relative), link=destination):
                    self.assertTrue((path.parent / unquote(target.path)).exists())

    def test_python_and_cpp_sdk_layout(self):
        package_dirs = sorted(path.name for path in (REPO_ROOT / "packages").iterdir() if path.is_dir())
        self.assertEqual(package_dirs, ["aorta"])
        language_dirs = sorted(path.name for path in (REPO_ROOT / "packages/aorta").iterdir() if path.is_dir())
        self.assertEqual(language_dirs, ["cpp", "python"])
        for language in language_dirs:
            for suffix in (".md", ".zh-CN.md"):
                self.assertTrue((REPO_ROOT / f"packages/aorta/{language}/README{suffix}").is_file())

    def test_cpp_recipe_sources_and_explicit_targets(self):
        for recipe in ("device-info", "subscribe-state", "service-call", "camera", "audio", "locomotion", "rcp-task"):
            directory = REPO_ROOT / "recipes" / recipe
            self.assertTrue((directory / "main.cc").is_file())
            build = (directory / "BUILD.bazel").read_text()
            self.assertIn('name = "main_cpp"', build)
            self.assertIn('tags = ["manual"]', build)
            for suffix in (".md", ".zh-CN.md"):
                links = document_links((directory / f"README{suffix}").read_text())
                self.assertIn("main.cc", links)
                self.assertIn(f"../../packages/aorta/cpp/README{suffix}", links)

    def test_development_area_navigation(self):
        areas = ("docs", "packages", "catalog", "recipes", "blueprints", "skills")
        for suffix in (".md", ".zh-CN.md"):
            homepage = (REPO_ROOT / f"README{suffix}").read_text()
            self.assertEqual(homepage.splitlines()[0], "# VBOT Lab")
            guide_links = document_links((REPO_ROOT / f"docs/README{suffix}").read_text())
            for folder in areas:
                with self.subTest(language=suffix, area=folder):
                    self.assertIn(f"{folder}/README{suffix}", document_links(homepage))
                    if folder != "docs":
                        self.assertIn(f"../{folder}/README{suffix}", guide_links)
            packages = (REPO_ROOT / f"packages/README{suffix}").read_text()
            self.assertIn(f"aorta/python/README{suffix}", document_links(packages))
            self.assertIn("Aorta Python SDK", packages)

    def test_python_sdk_installation_downloads_missing_dependency(self):
        install_scripts = []
        for suffix in (".md", ".zh-CN.md"):
            page = (REPO_ROOT / f"packages/aorta/python/README{suffix}").read_text()
            setup = page.split("## 3.", 1)[0]
            scripts = re.findall(r"```bash\n(.*?)```", setup, re.S)
            self.assertEqual(len(scripts), 1)
            script = scripts[0]
            install_scripts.append(script)
            result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("python -m pip install", script)
            self.assertNotIn("--no-index", script)
            self.assertIn('"flatbuffers==25.12.19"', script)
            self.assertNotIn("flatbuffers-25.12.19-py2.py3-none-any.whl", script)
            self.assertIn("python -m pip check", script)
            for package in ("aorta_sdk-2026.9.23", "aorta_msgs-2026.9.23", "vbot_edu_msgs-2026.9.24"):
                self.assertIn(f"artifacts/edu-sdk-2026.9.24/{package}", script)
            self.assertIn("PyPI", setup)
            self.assertIn(f"../../../docs/development/python-deployment{suffix}", document_links(setup))
            for obsolete in ("A release attaches four wheels", "每个 Release 附带四个 wheel"):
                self.assertNotIn(obsolete, setup)
        self.assertEqual(install_scripts[0], install_scripts[1])

    def test_python_deployment_has_explicit_transfer_and_device_runtime(self):
        blocks = []
        for suffix in (".md", ".zh-CN.md"):
            page = (REPO_ROOT / f"docs/development/python-deployment{suffix}").read_text()
            scripts = re.findall(r"```bash\n(.*?)```", page, re.S)
            self.assertEqual(len(scripts), 4)
            blocks.append(scripts)
            for script in scripts:
                result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            for required in ("tar -czf", "recipes/common.py", "recipes/observe.py", "scp",
                             "mktemp -d /userdata/vbot/apps/", "sha256sum -c SHA256SUMS",
                             "python3 -m venv .venv", "--no-index --find-links wheelhouse",
                             "python -m recipes.subscribe-state.main --execute"):
                self.assertIn(required, page)
            self.assertIn("python3 -m pip download --only-binary=:all: --no-deps", scripts[0])
            self.assertIn('--dest artifacts/wheelhouse "flatbuffers==25.12.19"', scripts[0])
            self.assertIn("PyPI", page)
            for recipe in (REPO_ROOT / "recipes").glob(f"*/README{suffix}"):
                body = recipe.read_text()
                self.assertIn(f"../../docs/development/python-deployment{suffix}", document_links(body))
                self.assertNotIn("device checkout root", body)
                self.assertNotIn("设备仓库根目录", body)
        self.assertEqual(blocks[0], blocks[1])

    def test_cpp_device_deployment_uses_binaries_not_bazel(self):
        blocks = []
        for suffix in (".md", ".zh-CN.md"):
            page = (REPO_ROOT / f"packages/aorta/cpp/README{suffix}").read_text()
            scripts = re.findall(r"```bash\n(.*?)```", page, re.S)
            blocks.append(scripts)
            for script in scripts:
                result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            for required in ("scp -r", "mktemp -d /userdata/vbot/apps/",
                             "sha256sum -c SHA256SUMS", "ldd ./bin/subscribe-state",
                             "./bin/subscribe-state --execute", "libaorta_core.so.12",
                             'cp -L "bazel-bin/recipes/$RECIPE/main_cpp"'):
                self.assertIn(required, page)
            self.assertNotIn("equipped ARM64 device", page)
            self.assertNotIn("如果 ARM64 设备具备构建环境", page)
            for recipe in (REPO_ROOT / "recipes").glob(f"*/README{suffix}"):
                body = recipe.read_text()
                self.assertNotIn("device equipped with Bazel", body)
                self.assertNotIn("具备 Bazel 的 ARM64 设备", body)
                self.assertNotRegex(body, r"bazel run [^\n]*:main_cpp[^\n]*--execute")
                self.assertIn(f"./bin/{recipe.parent.name}", body)
        self.assertEqual(blocks[0], blocks[1])

    def test_recipe_task_index(self):
        lessons = ("sensors", "camera", "perception", "audio", "locomotion", "system-peripherals", "rcp-task", "slam")
        for suffix in (".md", ".zh-CN.md"):
            index = (REPO_ROOT / f"recipes/README{suffix}").read_text()
            links = document_links(index)
            positions = []
            for lesson in lessons:
                link = f"{lesson}/README{suffix}"
                self.assertIn(link, links)
                positions.append(links.index(link))
                page = (REPO_ROOT / "recipes" / link).read_text()
                self.assertIn(f"../README{suffix}", document_links(page))
            self.assertEqual(positions, sorted(positions))
            self.assertIn(f"../packages/README{suffix}", links)
            self.assertIn(f"../blueprints/README{suffix}", links)

    def test_no_legacy_delivery_paths(self):
        for directory in ("sdk", "examples", "tutorials"):
            self.assertFalse((REPO_ROOT / directory).exists())
        for path in markdown_files():
            for destination in document_links(path.read_text()):
                target = urlsplit(destination.strip("<>"))
                if target.scheme or target.netloc:
                    continue
                parts = Path(unquote(target.path)).parts
                with self.subTest(file=str(path.relative_to(REPO_ROOT)), link=destination):
                    self.assertNotIn("sdk", parts)
                    self.assertNotIn("examples", parts)
                    self.assertNotIn("tutorials", parts)

    def test_devcontainer_configuration(self):
        path = REPO_ROOT / ".devcontainer/devcontainer.json"
        config = json.loads(path.read_text())
        self.assertEqual(config["service"], "dev")
        self.assertEqual(config["workspaceFolder"], "/workspace")
        self.assertTrue((path.parent / config["dockerComposeFile"]).is_file())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    # Keep runfiles paths lexical: individual files can point outside the tree.
    REPO_ROOT = args.root.absolute()
    unittest.main(argv=[__file__], verbosity=2)
