#!/usr/bin/env python3
"""Rewrites every absolute symlink under a directory as an equivalent
relative one.

Debian packages link their .so files with absolute targets (e.g.
libm.so -> /lib/aarch64-linux-gnu/libm.so.6), which resolve correctly on
a real installed system but break in a sysroot directory that isn't an
actual chroot: the OS follows the literal absolute path against the real
filesystem root, not the sysroot, and fails to find it.

Usage: fix_absolute_symlinks.py <sysroot_dir>
"""

import os
import sys
from pathlib import Path


def fix_absolute_symlinks(root: Path) -> int:
    root_str = str(root.resolve())
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_str):
        for name in filenames + dirnames:
            path = Path(dirpath) / name
            if path.is_symlink():
                target = os.readlink(path)
                if target.startswith("/"):
                    new_target = os.path.relpath(root_str + target, dirpath)
                    path.unlink()
                    path.symlink_to(new_target)
                    count += 1
    return count


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <sysroot_dir>")
    fixed_count = fix_absolute_symlinks(Path(sys.argv[1]))
    print(f"Fixed {fixed_count} absolute symlinks")
