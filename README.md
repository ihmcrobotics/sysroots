# sysroots

Minimal, versioned cross-compilation sysroots for robot onboard compute,
published as hash-pinned release tarballs for Bazel (`toolchains_llvm`) to
consume across projects (spot-drivers, orl-robot-drivers, whatever's next).

Each subdirectory is one target platform, containing only a `Dockerfile`
(plus any small helper scripts it needs) that builds that platform's
sysroot. Nothing here is checked in as built binaries -- a sysroot is only
ever committed as a *recipe*; the actual artifact is published as a
GitHub Release tarball, built by CI from that recipe.

## Platforms

- **`jetpack-5.1.2-aarch64`** -- NVIDIA Jetson boards running JetPack
  5.1.2 (L4T R35.4.1, Ubuntu 20.04 Focal, glibc 2.31). Used for
  cross-compiling robot driver binaries deployed to a Jetson attached to
  the robot.

## Building locally

```
docker buildx build --target sysroot --output type=tar,dest=sysroot.tar jetpack-5.1.2-aarch64
gzip -9 sysroot.tar
sha256sum sysroot.tar.gz
```

No `qemu`/`binfmt_misc` setup needed: the only step that touches arm64
binaries is `apt-get download`, which fetches `.deb` files without
executing anything in them.

## Publishing a release

Currently manual: run the `Build jetpack-5.1.2-aarch64 sysroot` GitHub
Actions workflow (`workflow_dispatch`, so trigger it from the Actions tab
or `gh workflow run`), giving it a version like `v1`. It builds the
sysroot, tars and gzips it, computes a `sha256`, and publishes both as a
GitHub Release tagged `jetpack-5.1.2-aarch64-v1`.

## Consuming from a downstream repo

In the consuming repo's `MODULE.bazel`:

```python
sysroot = use_repo_rule("@toolchains_llvm//toolchain:sysroot.bzl", "sysroot")

sysroot(
    name = "jetson_sysroot",
    url = "https://github.com/<org>/sysroots/releases/download/jetpack-5.1.2-aarch64-v1/sysroot.tar.gz",
    sha256 = "<sha256 from the release page>",
)

llvm.sysroot(
    name = "llvm_toolchain",
    targets = ["linux-aarch64"],
    label = "@jetson_sysroot//:sysroot",
)
```

This replaces a hardcoded local filesystem path with a hash-pinned fetch
-- every machine (and CI, eventually) gets byte-identical sysroot
content, verified against the recorded `sha256`, no per-machine path
setup.

## Adding a new platform

Add a new top-level directory (e.g. `go2-focal-aarch64/`) with its own
`Dockerfile` and a matching workflow under `.github/workflows/`. Release
tags are namespaced by platform (`<platform>-v<N>`), so multiple
platforms' version histories can coexist in this one repo without
colliding.
