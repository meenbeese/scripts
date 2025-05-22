#!/usr/bin/env python3
"""
Import Statement Organizer for Java/Kotlin Projects

This script organizes and sorts import statements in Java and Kotlin files according to a predefined order.
It maintains proper grouping and spacing between different package groups (android, androidx, etc).

Features:
- Groups imports by their top-level package name (android, androidx, etc)
- Keeps static imports at the top
- Maintains separation between different package groups with blank lines
- Automatically adds semicolons for Java files
- Detects and warns about star imports (import foo.*)
- Preserves existing code structure outside of import blocks

Usage:
    python organize_imports.py [--app DIR] [--src DIR]

    --app DIR    Directory containing Java/Kotlin files (default: ./app)
    --src DIR    Alternative source directory to scan

Example:
    python organize_imports.py --app ./myproject/app
    python organize_imports.py --src ./src/main/java
"""

import os
import re
import argparse
from collections import defaultdict

PACKAGE_RE = re.compile(r"^package\s+[\w\.]+;?\s*$")

IMPORT_RE = re.compile(r"^(import\s+static|import)\s+([\w\.\*]+)(;)?", re.MULTILINE)

SUPPORTED_EXTENSIONS = (".java", ".kt")

IMPORT_ORDER = [
    "static",
    "android",
    "androidx",
    "com",
    "net",
    "org",
    "kotlin",
    "kotlinx",
    "java",
    "javax",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Organize and sort import statements in Java/Kotlin files."
    )
    parser.add_argument(
        "--app",
        default="./app",
        help="Directory containing Java/Kotlin files (default: ./app)",
    )
    parser.add_argument("--src", help="Alternative source directory to scan")
    return parser.parse_args()


def get_import_group(import_path, is_static):
    if is_static:
        return "static"

    top_level = import_path.split(".")[0]

    if top_level in IMPORT_ORDER:
        return top_level

    return "zzz_other." + import_path


def sort_imports(imports):
    # First group by top-level package according to IMPORT_ORDER
    groups = defaultdict(list)
    for is_static, path, line in imports:
        if is_static:
            groups["static"].append((path, line))
            continue

        top = path.split(".")[0]
        # Use the exact group from IMPORT_ORDER
        for order_group in IMPORT_ORDER:
            if top == order_group:
                groups[order_group].append((path, line))
                break
        else:
            groups["zzz_other"].append((path, line))

    ordered = []

    for group in IMPORT_ORDER:
        if group in groups and groups[group]:
            ordered.extend([line for _, line in sorted(groups[group])])
            ordered.append("")
    if "zzz_other" in groups and groups["zzz_other"]:
        ordered.extend([line for _, line in sorted(groups["zzz_other"])])
        ordered.append("")

    # Remove trailing blank lines
    while ordered and ordered[-1] == "":
        ordered.pop()

    return ordered


def process_file(filepath):
    # Get relative path for cleaner output
    rel_path = os.path.relpath(filepath, os.path.dirname(APP_DIR))
    print(f"\nProcessing {rel_path}")
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    imports = []
    import_lines = []
    star_imports = []
    package_idx = -1

    for idx, line in enumerate(lines):
        line = line.strip()

        if not line or line.startswith("//"):
            continue

        if PACKAGE_RE.match(line):
            package_idx = idx
            continue

        import_match = IMPORT_RE.match(line)
        if import_match:
            is_static = import_match.group(1) == "import static"
            path = import_match.group(2)

            if "*" in path:
                star_imports.append((line, idx + 1))

            if filepath.endswith(".java") and not line.endswith(";"):
                line = line + ";"
            imports.append((is_static, path, line))
            import_lines.append(idx)

    if not imports:
        return

    first = import_lines[0]
    last = import_lines[-1]

    sorted_imports = sort_imports(imports)
    next_content_idx = last + 1
    preserved_lines = []
    while next_content_idx < len(lines):
        current_line = lines[next_content_idx].rstrip("\n")
        if current_line.strip() and not current_line.strip().startswith("//"):
            break
        if current_line.strip():
            preserved_lines.append(lines[next_content_idx])
        next_content_idx += 1

    preserved_lines.append("\n")

    if package_idx != -1:
        new_lines = (
            lines[: package_idx + 1]
            + ["\n"]
            + [s + "\n" for s in sorted_imports]
            + preserved_lines
            + lines[next_content_idx:]
        )
    else:
        new_lines = (
            lines[:first]
            + [s + "\n" for s in sorted_imports]
            + preserved_lines
            + lines[next_content_idx:]
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Reformatted imports in {rel_path}")


def scan_and_process():
    found_imports = False
    star_import_files = []
    processed_files = 0
    processed_imports = 0
    unique_dirs = set()

    for root, _, files in os.walk(APP_DIR):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                filepath = os.path.join(root, file)
                unique_dirs.add(os.path.dirname(filepath))
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    import_count = content.count("import ")
                    if import_count > 0:
                        found_imports = True
                        processed_imports += import_count
                        processed_files += 1
                        if "*" in content:
                            star_import_files.append(filepath)
                process_file(filepath)

    if not found_imports:
        print("\n⚠️ No imports found in any files in the specified directory.")
        return

    if star_import_files:
        print("\n⚠️ Star Import Warnings:")
        print(
            "The following files contain star imports (*), which are considered bad practice:"
        )
        for filepath in star_import_files:
            rel_path = os.path.relpath(filepath, os.path.dirname(APP_DIR))
            print(f"  • {rel_path}")

    print(
        f"\n📊 Summary: Processed {processed_imports} imports in {processed_files} files across {len(unique_dirs)} directories."
    )


if __name__ == "__main__":
    args = parse_args()
    APP_DIR = args.app if args.app else "./app"
    if args.src:
        APP_DIR = args.src

    scan_and_process()
    input("\nPress Enter to exit...")
