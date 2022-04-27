import argparse
import os
import re
from dataclasses import dataclass, field
from typing import List

import jsonref
import yaml
from jinja2 import Environment, FileSystemLoader

# TODO:
#   - Handle allOf
#   - Format descriptions as markdowns
#   - items.example for string items


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

    def nest_level(self):
        p = self
        level = 0

        while p.parent:
            level += 1
            p = p.parent

        return level


def _yaml_load(path):
    with open(path, "r") as f:
        return yaml.safe_load(f.read())


def extract_default(s):
    r = re.findall(r"Default value is (\w+)\b", s)

    if r:
        return r[0]

    return ""


parser = argparse.ArgumentParser()
parser.add_argument("--schema-dir", type=str, required=True, help="Path to the schema dir")
parser.add_argument("--root", type=str, required=True, help="Root object")

args = parser.parse_args()

print("Loading schema...")
schema_all = jsonref.load_uri(
    args.root,
    base_uri=args.schema_dir,
    loader=_yaml_load,
)
required = schema_all["required"]


def load_properties(obj, root, option: int = 0):
    props = []

    required = obj.get("required", [])

    for name in obj["properties"]:
        prop = obj["properties"][name]

        p = Property(
            name=name,
            type=prop.get("type", "?"),
            deprecated=prop.get("deprecated", False),
            description=prop.get("description", ""),
            default=extract_default(prop.get("description", "")),
            example=prop.get("example"),
            properties=[],
            parent=root,
            required=name in required,
            option=option,
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

        if prop.get("enum"):
            p.enum = prop["enum"]

        props.append(p)

        if prop.get("items", {}).get("oneOf"):
            for n, opt in enumerate(prop["items"]["oneOf"]):
                props += load_properties(opt, p, n + 1)

        if prop.get("items", {}).get("anyOf"):
            for n, opt in enumerate(prop["items"]["anyOf"]):
                props += load_properties(opt, p, n + 1)

        # Load children
        if "properties" in prop:
            props += load_properties(prop, p)

        if "items" in prop and "properties" in prop["items"]:
            props += load_properties(prop["items"], p)

    return props


print("Gathering data...")
data = {"properties": []}

root = Property("<root>", schema_all["type"], False, schema_all["description"], "")
data["properties"].append(root)
data["properties"] = load_properties(schema_all, root)

print("Rendering...")

# Render
loader = FileSystemLoader("templates")
env = Environment(loader=loader)
template = env.get_template("index.html")
output = template.render(data)

os.makedirs("build", exist_ok=True)

with open("build/index.html", "w") as fwrite:
    fwrite.write(output)

print("Output written to: build/index.html")
