#!/usr/bin/env python3
"""Import Apify API keys from a text file into the JSON key pool.

Input format: one token per line, # comments supported.

Usage:
    python scripts/import_apify_keys.py --input keys.txt
    python scripts/import_apify_keys.py --input keys.txt --output AIM/data/apify_keys.json
    python scripts/import_apify_keys.py --input keys.txt --label-prefix acc --merge
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Import Apify API keys into key pool JSON")
    parser.add_argument("--input", required=True, help="Text file with one token per line")
    parser.add_argument("--output", default="AIM/data/apify_keys.json", help="Output JSON file")
    parser.add_argument(
        "--label-prefix", default="account",
        help="Label prefix (e.g. 'account' → 'account-001')",
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="Merge into existing file instead of overwriting",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    tokens = []
    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens.append(line)

    if not tokens:
        print("Error: no tokens found in input file", file=sys.stderr)
        sys.exit(1)

    new_keys = []
    for i, token in enumerate(tokens, start=1):
        new_keys.append({
            "token": token,
            "status": "active",
            "exhausted_at": None,
            "label": f"{args.label_prefix}-{i:03d}",
        })

    if args.merge and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        existing.setdefault("keys", []).extend(new_keys)
        data = existing
    else:
        data = {"keys": new_keys}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Imported {len(tokens)} keys → {output_path}")
    print(f"  Total keys in file: {len(data['keys'])}")


if __name__ == "__main__":
    main()
