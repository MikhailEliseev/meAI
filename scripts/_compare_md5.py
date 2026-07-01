#!/usr/bin/env python3
"""Compare md5 lists between local and server, report drift."""
import sys


def parse(path):
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                md5, fname = parts
                result[fname] = md5
    return result


def main():
    local = parse('/tmp/local_md5_full.txt')
    server = parse('/tmp/server_md5_full.txt')

    local_only = set(local) - set(server)
    server_only = set(server) - set(local)
    both = set(local) & set(server)

    same = [f for f in both if local[f] == server[f]]
    diff = [f for f in both if local[f] != server[f]]

    print(f"=== SYNC REPORT ===")
    print(f"Local:  {len(local)} files")
    print(f"Server: {len(server)} files")
    print(f"Identical:  {len(same)} files ({100 * len(same) / max(len(both), 1):.0f}%)")
    print(f"Different:  {len(diff)} files")
    print(f"Only local:  {len(local_only)} files")
    print(f"Only server: {len(server_only)} files")
    print()

    if diff:
        print(f"=== DIFFERENT ({len(diff)} files) ===")
        for f in sorted(diff):
            print(f"  ⚠️ {f}")
            print(f"     local={local[f]}")
            print(f"     server={server[f]}")
        print()

    if local_only:
        print(f"=== ONLY LOCAL ({len(local_only)} files) ===")
        for f in sorted(local_only):
            print(f"  + {f}")
        print()

    if server_only:
        print(f"=== ONLY SERVER ({len(server_only)} files) ===")
        for f in sorted(server_only):
            print(f"  - {f}")
        print()

    # Exit 1 if drift, 0 if all in sync
    return 0 if not (diff or local_only or server_only) else 1


if __name__ == '__main__':
    sys.exit(main())
