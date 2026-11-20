"""Optional, locally supplied D-Robotics S100 multimedia SDK; no downloads."""

def _impl(ctx):
    directory = ctx.os.environ.get("VBOT_S100_MULTIMEDIA_DIR", "")
    markers = [
        "include/hb_media_codec.h",
        "include/hb_media_basic_types.h",
        "include/hb_media_error.h",
        "lib/libmultimedia.so",
        "lib/libhbmem.so.1",
        "lib/libalog.so.1",
    ]
    if not directory.startswith("/") or not all([ctx.path(directory + "/" + name).exists for name in markers]):
        ctx.file("missing.bzl", 'def _impl(ctx):\n    fail("Set VBOT_S100_MULTIMEDIA_DIR to a matching S100 SDK directory; see recipes/camera/README.md")\nmissing_sdk = rule(implementation = _impl)\n')
        ctx.file("BUILD.bazel", '''
load(":missing.bzl", "missing_sdk")
package(default_visibility = ["//visibility:public"])
missing_sdk(name = "headers")
missing_sdk(name = "codec")
''')
        return
    ctx.symlink(directory + "/include", "include")
    ctx.symlink(directory + "/lib", "lib")
    ctx.file("BUILD.bazel", '''
package(default_visibility = ["//visibility:public"])
cc_library(name = "headers", hdrs = glob(["include/**/*.h"]), includes = ["include"])
cc_import(name = "multimedia", shared_library = "lib/libmultimedia.so")
cc_import(name = "hbmem", shared_library = "lib/libhbmem.so.1")
cc_import(name = "alog", shared_library = "lib/libalog.so.1")
cc_library(
    name = "codec",
    deps = [":headers", ":multimedia", ":hbmem", ":alog"],
    target_compatible_with = ["@platforms//os:linux", "@platforms//cpu:aarch64"],
)
''')

s100_multimedia_repository = repository_rule(
    implementation = _impl,
    environ = ["VBOT_S100_MULTIMEDIA_DIR"],
    local = True,
)
