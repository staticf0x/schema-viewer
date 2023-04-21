"""Loader for schema properties."""
import os

import jsonref
import yaml

from schema_viewer.helpers import extract_default, format_description
from schema_viewer.property import Property


def parse_array(p: Property, prop: dict) -> None:
    """Parse `array` type."""
    items = prop["items"]

    if items.get("type"):
        # Type of child items
        p.type = f"array[{items['type']}]"

    if items.get("enum"):
        parse_enum(p, items)

    p.min_items = prop.get("minItems", 0)
    p.max_items = prop.get("maxItems", 0)

    if items.get("pattern"):
        p.pattern = items["pattern"]

    if items.get("example") and not p.example:
        p.example = items["example"]


def parse_enum(p: Property, prop: dict) -> None:
    """Parse `enum` properties."""
    p.enum = prop["enum"]


def load_properties(obj: Property, root: Property, option: int = 0, condition: str = ""):
    """Load properties for an object."""
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
            pattern=prop.get("pattern"),
            option=option,
            condition=condition,
        )

        if p.type == "array":
            parse_array(p, prop)

        if prop.get("enum"):
            parse_enum(p, prop)

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


def _yaml_load(path: str):
    """Loader function for the schema."""
    with open(path) as f:
        return yaml.safe_load(f.read())


class Loader:
    """A class for loading all schema properties."""

    def __init__(self, root: str, schema_dir: str) -> None:
        self.root = root
        self.schema_dir = schema_dir

        # Infer root node name from root schema path
        self.root_name = os.path.splitext(os.path.basename(self.root))[0]

    def load_properties(self) -> list:
        """Load all properties from the schema."""
        schema_all = jsonref.load_uri(
            self.root,
            base_uri=self.schema_dir,
            loader=_yaml_load,
        )

        root = Property(
            name=self.root_name,
            type=schema_all["type"],
            description=schema_all["description"],
        )

        properties = [root]
        properties += load_properties(schema_all, root)

        return properties
