"""Consume locally extracted release artifacts for C++ recipes."""

def _release_impl(ctx):
    sdk = ctx.os.environ.get("AORTA_CPP_SDK_DIR", "")
    schema = ctx.os.environ.get("AORTA_EDU_SCHEMA_DIR", "")
    for name, path, marker in [
        ("AORTA_CPP_SDK_DIR", sdk, "lib/libaorta_cpp.a"),
        ("AORTA_EDU_SCHEMA_DIR", schema, "include/execute_task_msg.h"),
    ]:
        if not path.startswith("/") or not ctx.path(path + "/" + marker).exists:
            # Runfiles/repository mapping may load this repository for unrelated
            # documentation tests. Fail only when a C++ SDK target is analyzed.
            message = "Set %s to the absolute extracted release directory; see packages/aorta/cpp/README.md" % name
            ctx.file("missing.bzl", "def _impl(ctx):\n    fail(%r)\nmissing_sdk = rule(implementation = _impl)\n" % message)
            ctx.file("BUILD.bazel", 'load(":missing.bzl", "missing_sdk")\nmissing_sdk(name = "sdk", visibility = ["//visibility:public"])\n')
            return
    ctx.symlink(sdk + "/include", "sdk_include")
    ctx.symlink(sdk + "/lib", "lib")
    ctx.symlink(schema + "/include", "edu_include")
    ffmpeg = ctx.os.environ.get("VBOT_FFMPEG_DIR", "")
    ffmpeg_build = 'cc_library(name = "ffmpeg", linkopts = ["-lavcodec", "-lavutil", "-lswscale"])\n'
    if ffmpeg:
        for marker in ["include/libavcodec/avcodec.h", "lib/libavcodec.so.58", "lib/libavutil.so.56", "lib/libswscale.so.5"]:
            if not ffmpeg.startswith("/") or not ctx.path(ffmpeg + "/" + marker).exists:
                fail("VBOT_FFMPEG_DIR must contain FFmpeg 4.4 headers and shared libraries: " + marker)
        ctx.symlink(ffmpeg + "/include", "ffmpeg_include")
        ctx.symlink(ffmpeg + "/lib", "ffmpeg_lib")
        ffmpeg_build = """
cc_import(name = "avcodec", shared_library = "ffmpeg_lib/libavcodec.so.58")
cc_import(name = "avutil", shared_library = "ffmpeg_lib/libavutil.so.56")
cc_import(name = "swscale", shared_library = "ffmpeg_lib/libswscale.so.5")
cc_library(
    name = "ffmpeg",
    hdrs = glob(["ffmpeg_include/**/*.h"]),
    includes = ["ffmpeg_include"],
    deps = [":avcodec", ":avutil", ":swscale"],
)
"""
    ctx.file("BUILD.bazel", """
package(default_visibility = ["//visibility:public"])
cc_import(name = "cpp", static_library = "lib/libaorta_cpp.a")
cc_import(name = "core", shared_library = "lib/libaorta_core.so.12")
cc_library(
    name = "sdk",
    hdrs = glob(["sdk_include/**/*.h", "sdk_include/**/*.hpp", "edu_include/**/*.h"]),
    includes = ["edu_include", "sdk_include"],
    deps = [":cpp", ":core"],
    linkopts = ["-pthread", "-ldl"],
)
""" + ffmpeg_build)

aorta_release_repository = repository_rule(
    implementation = _release_impl,
    environ = ["AORTA_CPP_SDK_DIR", "AORTA_EDU_SCHEMA_DIR", "VBOT_FFMPEG_DIR"],
    local = True,
)
