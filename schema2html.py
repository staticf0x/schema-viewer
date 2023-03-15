import argparse
import os
from dataclasses import dataclass, field
from typing import List

import jsonref
import yaml
from devtools import debug
from jinja2 import Environment, FileSystemLoader

from schema_viewer.helpers import extract_default, format_description

# TODO:
#   - Format descriptions as markdowns


@dataclass
class Property:
    name: str
    type: str
    deprecated: bool
    description: str = ""
    default: str = ""
    example: str = ""
    properties: List = field(default_factory=list)
    parent: object = None
    min_items: int = 0
    max_items: int = 0
    enum: List = field(default_factory=list)
    required: bool = False
    pattern: str = ""
    option: int = 0
    condition: str = ""

    def nest_level(self):
        p = self
        level = 0

        while p.parent:
            level += 1
            p = p.parent

        return level

    @property
    def path(self):
        parts = []
        p = self

        while p.parent:
            parts.append(p.name)
            p = p.parent
        else:
            parts.append(p.name)

        return " » ".join(parts[::-1])


def _yaml_load(path):
    with open(path, "r") as f:
        return yaml.safe_load(f.read())


def load_properties(obj, root, option: int = 0, condition: str = ""):
    props = []

    required = obj.get("required", [])

    for name in obj["properties"]:
        prop = obj["properties"][name]

        description = format_description(prop.get("description", ""))

        p = Property(
            name=name,
            type=prop.get("type", "?"),
            deprecated=prop.get("deprecated", False),
            description=description.strip(),
            default=extract_default(prop.get("description", "")),
            example=prop.get("example"),
            properties=[],
            parent=root,
            required=name in required,
            option=option,
            condition=condition,
        )

        if p.type == "array":
            items = prop["items"]

            if items.get("type"):
                p.type = f"array[{items['type']}]"

            if items.get("enum"):
                enum_values = items["enum"]
                p.enum = enum_values

            p.min_items = prop.get("minItems", 0)
            p.max_items = prop.get("maxItems", 0)

            if items.get("pattern"):
                p.pattern = items["pattern"]

            if items.get("example") and not p.example:
                p.example = items["example"]

        if prop.get("enum"):
            p.enum = prop["enum"]

        props.append(p)

        if prop.get("items"):
            items = prop["items"]

            if items.get("oneOf"):
                for n, opt in enumerate(prop["items"]["oneOf"]):
                    props += load_properties(opt, p, n + 1)

            if items.get("anyOf"):
                for n, opt in enumerate(prop["items"]["anyOf"]):
                    props += load_properties(opt, p, n + 1)

            if items.get("allOf"):
                for n, opt in enumerate(prop["items"]["allOf"]):
                    if "if" in opt:
                        condition = "if: "

                        for field_name, cond in opt["if"]["properties"].items():
                            condition += f"{field_name}={cond['const']}"

                        props += load_properties(opt["then"], p, n + 1, condition)
                    else:
                        props += load_properties(opt, p, n + 1)

        if prop.get("oneOf"):
            for n, opt in enumerate(prop["oneOf"]):
                props += load_properties(opt, p, n + 1)

        if prop.get("anyOf"):
            for n, opt in enumerate(prop["anyOf"]):
                props += load_properties(opt, p, n + 1)

        if prop.get("allOf"):
            for n, opt in enumerate(prop["allOf"]):
                if "if" in opt:
                    condition = "if: "

                    for field_name, cond in opt["if"]["properties"].items():
                        condition += f"{field_name}={cond.get('const', 'Any')}"

                    if "then" in opt:
                        props += load_properties(opt["then"], p, n + 1, condition)
                else:
                    props += load_properties(opt, p, n + 1)

        # Load children
        if "properties" in prop:
            props += load_properties(prop, p)

        if "items" in prop and "properties" in prop["items"]:
            props += load_properties(prop["items"], p)

    return props


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-dir", type=str, required=True, help="Path to the schema dir")
    parser.add_argument("--root", type=str, required=True, help="Root object")
    parser.add_argument("--format", type=str, choices=["html", "md"], default="html", help="Output format")

    args = parser.parse_args()

    print("Loading schema...")
    schema_all = jsonref.load_uri(
        args.root,
        base_uri=args.schema_dir,
        loader=_yaml_load,
    )
    required = schema_all["required"]

    print("Gathering data...")
    data = {"properties": []}

    root_name = os.path.splitext(os.path.basename(args.root))[0]

    root = Property(root_name, schema_all["type"], False, schema_all["description"], "")
    data["properties"].append(root)
    data["properties"] = load_properties(schema_all, root)

    print("Rendering...")

    # Render
    loader = FileSystemLoader("templates")
    env = Environment(loader=loader)

    match args.format:
        case "html":
            template = env.get_template("index.html")
            output_path = os.path.join("build", f"{root_name}.html")
        case "md":
            template = env.get_template("index.md")
            output_path = os.path.join("build", f"{root_name}.md")

    output = template.render(data)

    os.makedirs("build", exist_ok=True)

    with open(output_path, "w") as fwrite:
        fwrite.write(output)

    print(f"Output written to: {output_path}")
