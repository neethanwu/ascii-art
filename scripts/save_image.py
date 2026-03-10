#!/usr/bin/env python3
"""Save an image to ascii/tmp/ for processing. Outputs the saved path to stdout."""

import os
import shutil
import sys
from datetime import datetime


def main():
    if len(sys.argv) < 2:
        print("Usage: save_image.py <source_path> [output_dir]", file=sys.stderr)
        print("Copies image to ascii/tmp/ with timestamped name.", file=sys.stderr)
        print("Prints saved path to stdout.", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.getcwd(), "ascii", "tmp")

    if not os.path.isfile(source):
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    # Preserve original extension
    ext = os.path.splitext(source)[1].lower() or ".png"
    timestamp = datetime.now().strftime("%H%M%S")
    dest = os.path.join(out_dir, f"input_{timestamp}{ext}")

    shutil.copy2(source, dest)
    # Output saved path — this is what the agent reads
    print(dest)


if __name__ == "__main__":
    main()
