"""Use the development image's Linux ARM64 GCC 11 compiler and target headers."""

load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:cc_toolchain_config_lib.bzl", "feature", "flag_group", "flag_set", "tool_path")

_COMPILE = [
    ACTION_NAMES.c_compile,
    ACTION_NAMES.cpp_compile,
    ACTION_NAMES.linkstamp_compile,
    ACTION_NAMES.assemble,
    ACTION_NAMES.preprocess_assemble,
    ACTION_NAMES.cpp_header_parsing,
]
_LINK = [
    ACTION_NAMES.cpp_link_executable,
    ACTION_NAMES.cpp_link_dynamic_library,
    ACTION_NAMES.cpp_link_nodeps_dynamic_library,
]

def _flags(name, actions, flags, enabled = True):
    return feature(
        name = name,
        enabled = enabled,
        flag_sets = [flag_set(actions = actions, flag_groups = [flag_group(flags = flags)])],
    )

def _impl(ctx):
    paths = {name: "/usr/bin/aarch64-linux-gnu-" + name for name in [
        "ar", "cpp", "gcc", "gcov", "ld", "nm", "objcopy", "objdump", "strip", "dwp",
    ]}
    return cc_common.create_cc_toolchain_config_info(
        ctx = ctx,
        toolchain_identifier = "vbot-linux-aarch64-gcc11",
        host_system_name = "x86_64-linux-gnu",
        target_system_name = "aarch64-linux-gnu",
        target_cpu = "aarch64",
        target_libc = "glibc",
        compiler = "gcc",
        abi_version = "aarch64",
        abi_libc_version = "glibc",
        tool_paths = [tool_path(name = name, path = path) for name, path in paths.items()],
        cxx_builtin_include_directories = [
            "/usr/lib/gcc-cross/aarch64-linux-gnu/11/include",
            "/usr/aarch64-linux-gnu/include/c++/11",
            "/usr/aarch64-linux-gnu/include/c++/11/aarch64-linux-gnu",
            "/usr/aarch64-linux-gnu/include/c++/11/backward",
            "/usr/aarch64-linux-gnu/include",
        ],
        features = [
            _flags("compile_defaults", _COMPILE, ["-fPIC", "-no-canonical-prefixes", "-fno-canonical-system-headers"]),
            # Bazel enables exactly the feature matching --compilation_mode/-c.
            _flags("fastbuild", _COMPILE, ["-O0"], enabled = False),
            _flags("opt", _COMPILE, ["-O2", "-DNDEBUG"], enabled = False),
            _flags("dbg", _COMPILE, ["-O0", "-g"], enabled = False),
            _flags("link_defaults", _LINK, ["-lstdc++", "-lm"]),
            feature(name = "supports_pic", enabled = True),
            feature(name = "supports_dynamic_linker", enabled = True),
        ],
    )

aarch64_gcc_config = rule(implementation = _impl, provides = [CcToolchainConfigInfo])
