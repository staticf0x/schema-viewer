"""Convert jsonschema YAMLs into a HTML or Markdown."""
import argparse
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from schema_viewer.loader import Loader

ROOT_DIR = Path(__file__).parent
TEMPLATES_DIR = ROOT_DIR / "templates"
BUILD_DIR = ROOT_DIR / "build"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-dir", type=str, required=True, help="Path to the schema dir")
    parser.add_argument("--root", type=str, required=True, help="Root object")
    parser.add_argument("--format", type=str, choices=["html", "md"], default="html", help="Output format")
    parser.add_argument("--title", type=str, help="Document title")

    args = parser.parse_args()

    print("Loading schema...")
    prop_loader = Loader(args.root, args.schema_dir)

    print("Gathering data...")
    data = {"properties": prop_loader.load_properties()}

    # Render
    print("Rendering...")

    loader = FileSystemLoader(TEMPLATES_DIR)
    env = Environment(loader=loader)

    match args.format:
        case "html":
            template = env.get_template("index.html")
            output_path = BUILD_DIR / f"{prop_loader.root_name}.html"
        case "md":
            template = env.get_template("index.md")
            output_path = BUILD_DIR / f"{prop_loader.root_name}.md"

    if args.title:
        data["title"] = args.title
    else:
        data["title"] = f"{prop_loader.root_name} schema"

    output = template.render(data)

    # Write output
    os.makedirs(BUILD_DIR, exist_ok=True)

    with open(output_path, "w") as fwrite:
        fwrite.write(output)

    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
