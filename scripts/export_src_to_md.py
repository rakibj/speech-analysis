from pathlib import Path

SRC_DIR = Path("src")
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "src_dump.md"


def generate_markdown_from_src():
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"{SRC_DIR} does not exist")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    py_files = sorted(SRC_DIR.rglob("*.py"))

    with OUTPUT_FILE.open("w", encoding="utf-8") as md:
        md.write("# Source Code Dump (src)\n\n")

        for py_file in py_files:
            relative_path = py_file.relative_to(SRC_DIR)

            md.write(f"## {relative_path}\n\n")
            md.write("```python\n")
            md.write(f"# {relative_path}\n\n")

            content = py_file.read_text(encoding="utf-8")
            md.write(content.rstrip())
            md.write("\n```\n\n")

    print(f"✅ Markdown generated at: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    generate_markdown_from_src()
