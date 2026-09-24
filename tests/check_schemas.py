"""Check that schemas/ carries exactly the public interfaces and what they need."""

import json
from pathlib import Path
import re
import unittest


SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
ROS2 = SCHEMAS / "ros2"
KINDS = ("msg", "srv", "action")
PRIMITIVES = {
    "bool", "byte", "char", "float32", "float64", "int8", "uint8", "int16", "uint16",
    "int32", "uint32", "int64", "uint64", "string", "wstring",
}
ACTION_DEPENDENCIES = {"action_msgs", "builtin_interfaces", "unique_identifier_msgs"}


def definition_files():
    return {
        (path.parts[-3], path.parts[-2], path.stem)
        for kind in KINDS
        for path in ROS2.glob(f"*/{kind}/*.{kind}")
    }


def referenced_types(package, text):
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line == "---":
            continue
        token = re.sub(r"<=\d+$", "", re.sub(r"\[[^\]]*\]$", "", line.split()[0]))
        if token in PRIMITIVES:
            continue
        parts = token.split("/")
        if len(parts) == 1:
            yield package, parts[0]
        elif len(parts) == 2:
            yield parts[0], parts[1]
        else:
            yield parts[0], parts[-1]


class SchemaTreeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = json.loads((ROS2 / "routes.json").read_text())
        cls.manifest = json.loads((SCHEMAS / "MANIFEST.json").read_text())
        cls.files = definition_files()

    def test_routes_name_public_schemas_and_types(self):
        ids = [route["id"] for route in self.routes["routes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), self.manifest["file_counts"]["routes"])
        for route in self.routes["routes"]:
            with self.subTest(route=route["id"]):
                self.assertIn(route["kind"], ("topic", "service", "action"))
                self.assertIn(route["direction"], ("aorta_to_ros", "ros_to_aorta"))
                self.assertTrue((SCHEMAS / route["aorta"]["schema"]).is_file())
                package, kind, name = route["ros"]["type"].split("/")
                self.assertEqual(kind, {"topic": "msg", "service": "srv", "action": "action"}[route["kind"]])
                if package not in self.routes["external_packages"]:
                    self.assertIn((package, kind, name), self.files)

    def test_definitions_are_closed_under_references(self):
        external = set()
        for package, kind, name in sorted(self.files):
            text = (ROS2 / package / kind / f"{name}.{kind}").read_text()
            if kind == "action":
                external |= ACTION_DEPENDENCIES
            for dep_package, dep_name in referenced_types(package, text):
                with self.subTest(definition=f"{package}/{kind}/{name}", field_type=f"{dep_package}/{dep_name}"):
                    if (ROS2 / dep_package).is_dir():
                        self.assertIn((dep_package, "msg", dep_name), self.files)
                    else:
                        external.add(dep_package)
        for route in self.routes["routes"]:
            package = route["ros"]["type"].split("/")[0]
            if not (ROS2 / package).is_dir():
                external.add(package)
        self.assertEqual(sorted(external), self.routes["external_packages"])

    def test_every_definition_is_used(self):
        # Each definition must be a route's type, referenced by another definition, or a
        # constant holder that documents a route's values. Anything else is an extra interface.
        used = {tuple(route["ros"]["type"].split("/")) for route in self.routes["routes"]}
        for package, kind, name in self.files:
            text = (ROS2 / package / kind / f"{name}.{kind}").read_text()
            used.update((dep_package, "msg", dep_name) for dep_package, dep_name in referenced_types(package, text))
        for package, kind, name in sorted(self.files - used):
            with self.subTest(definition=f"{package}/{kind}/{name}"):
                text = (ROS2 / package / kind / f"{name}.{kind}").read_text()
                fields = [line for line in (raw.split("#", 1)[0].strip() for raw in text.splitlines())
                          if line and "=" not in line]
                self.assertEqual(fields, [], "neither used by a route nor a constant holder")

    def test_manifest_counts_match_the_tree(self):
        counts = {}
        for package, kind, _ in self.files:
            counts.setdefault(package, {k: 0 for k in KINDS})[kind] += 1
        self.assertEqual(self.manifest["file_counts"]["ros2"], dict(sorted(counts.items())))
        fbs = list((SCHEMAS / "aorta/schemas").rglob("*.fbs"))
        self.assertEqual(self.manifest["file_counts"]["aorta_fbs"], len(fbs))
        pack = self.manifest["schema_pack"]
        self.assertRegex(pack["asset"], r"^aorta-edu-schema-pack-[0-9.]+-v4\.tar\.zst$")
        self.assertRegex(pack["sha256"], r"^[0-9a-f]{64}$")

    def test_licenses_accompany_the_definitions(self):
        for path in ("aorta/LICENSE", "aorta/NOTICE"):
            self.assertTrue((SCHEMAS / path).is_file(), path)
        notices = (ROS2 / "THIRD_PARTY_NOTICES.txt").read_text()
        for package in ("foxglove_msgs", "vision_msgs"):
            if (ROS2 / package).is_dir():
                self.assertIn(f"\n{package}/\n", notices)
        for relative in re.findall(r"see (\S+)", notices):
            self.assertTrue((ROS2 / relative).resolve().is_file(), relative)


if __name__ == "__main__":
    unittest.main()
