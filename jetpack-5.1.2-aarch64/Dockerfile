# syntax=docker/dockerfile:1
#
# Minimal aarch64 sysroot for cross-compiling C++ targeting NVIDIA Jetson
# boards running JetPack 5.1.2 (L4T R35.4.1, Ubuntu 20.04 Focal, glibc
# 2.31). Ships only the headers/libraries needed to link a C++ binary
# against glibc/libstdc++ -- not a full OS rootfs.
#
# Build + export (produces an uncompressed tar of the sysroot content,
# rooted at "/" -- no wrapping directory, so consumers extract with
# --strip-components 0):
#   docker buildx build --target sysroot --output type=tar,dest=sysroot.tar .
#
# GCC 10's libstdc++ is fetched alongside the default GCC 9 packages:
# Focal's default GCC 9.4 headers predate full C++20/23 stdlib support
# (e.g. <compare>), but Focal's libstdc++6 *runtime* package is already
# 10.x, so only the GCC 10 *headers*/static lib are missing by default.
#
# `apt-get download` only downloads .deb files, it never executes arm64
# code, so no qemu/binfmt_misc is needed anywhere in this build even
# though the fetched packages are arm64.

# Base rootfs: referenced only via COPY --from in the "assemble" stage
# below, never given a RUN step itself -- so pulling it needs no
# emulation, only the "fetch_debs"/"assemble" stages (both native
# x86_64) ever execute anything.
ARG BASE_ROOTFS_PLATFORM=linux/arm64
FROM --platform=$BASE_ROOTFS_PLATFORM ubuntu:20.04 AS base_rootfs

FROM ubuntu:20.04 AS fetch_debs
RUN dpkg --add-architecture arm64 && \
    sed -i "s/^deb /deb [arch=amd64] /" /etc/apt/sources.list && \
    printf '%s\n' \
        "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports focal main universe" \
        "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports focal-updates main universe" \
        "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports focal-security main universe" \
        > /etc/apt/sources.list.d/arm64-ports.list && \
    apt-get update -qq
RUN mkdir /debs && cd /debs && apt-get download \
    libc6:arm64 libc6-dev:arm64 linux-libc-dev:arm64 libc-dev-bin:arm64 \
    libgcc-s1:arm64 libgcc-9-dev:arm64 gcc-9-base:arm64 \
    libgcc-10-dev:arm64 gcc-10-base:arm64 \
    libstdc++6:arm64 libstdc++-9-dev:arm64 libstdc++-10-dev:arm64 \
    zlib1g:arm64 zlib1g-dev:arm64

# Assembles the sysroot: base rootfs + extracted dev packages, then two
# fixes needed for cross-linking to work (both confirmed necessary by
# real link failures -- see this repo's README):
#   1. Remove the fully-static glibc archives (mixing a static
#      libpthread.a with a dynamic libc.so fails to link on undefined
#      internal symbols like _dl_stack_flags).
#   2. Rewrite absolute symlinks to relative (see
#      fix_absolute_symlinks.py's own docstring).
FROM ubuntu:20.04 AS assemble
COPY --from=base_rootfs / /sysroot/
COPY --from=fetch_debs /debs /debs
RUN for deb in /debs/*.deb; do dpkg-deb -x "$deb" /sysroot; done && rm -rf /debs

# Debian ships both the fully-static archive and the matching shared
# library for these; our binaries link dynamically, and these .a files
# are only safe to link when *every* glibc piece is static together.
# Removing them forces the linker to always pick the matching .so.
# libc_nonshared.a is a small stub required even for dynamic linking,
# and is deliberately not in this list.
RUN cd /sysroot/usr/lib/aarch64-linux-gnu && \
    rm -f libc.a libpthread.a libm.a libdl.a librt.a libutil.a \
          libresolv.a libnsl.a libanl.a libBrokenLocale.a libmcheck.a \
          librpcsvc.a libg.a

COPY fix_absolute_symlinks.py /fix_absolute_symlinks.py
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends python3 && \
    python3 /fix_absolute_symlinks.py /sysroot && \
    rm /fix_absolute_symlinks.py

# Final stage: just the sysroot content, nothing else -- so
# `--output type=tar` exports exactly this and no base-image cruft.
FROM scratch AS sysroot
COPY --from=assemble /sysroot /
