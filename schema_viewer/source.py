"""Read source files into a source map."""
from dataclasses import dataclass
from pathlib import Path

from yaml import (
    BlockEndToken,
    BlockMappingStartToken,
    BlockSequenceStartToken,
    KeyToken,
    ScalarToken,
    scan,
)


@dataclass
class SourceProperty:
    """Class for data about the source property."""

    name: str
    path: str
    file: str
    line: int


def get_property_source_map(root: Path, file: str, path: str) -> dict[str, SourceProperty]:
    """Get a dict mapping between property path and the source property from the YAML."""
    key = None  # Whether we're reading a key
    properties = False  # Whether we're inside the properties block
    ref = None  # Whether we're reading a referenced file
    block = 0  # Current block during iteration
    props_block = 2  # Where the keys are located
    prop_map = {}  # Output dict

    with open(root / file) as f:
        tokens = list(scan(f.read()))

        for token in tokens:
            if isinstance(token, BlockMappingStartToken) or isinstance(
                token, BlockSequenceStartToken
            ):
                block += 1

            if isinstance(token, BlockEndToken):
                block -= 1

            if isinstance(token, KeyToken):
                key = token

            if isinstance(token, ScalarToken):
                if key:
                    # Previous token was KeyToken
                    if token.value == "properties" and not properties:
                        properties = True

                    if properties and token.value != "properties" and block == props_block:
                        path_to_prop = f"{path}.{token.value}"

                        prop = SourceProperty(
                            token.value, path_to_prop, file, token.start_mark.line + 1
                        )
                        prop_map[path_to_prop] = prop

                    if token.value == "$ref":
                        ref = True
                        continue

                    if ref:
                        ref_file = token.value
                        prop_map |= get_property_source_map(root, ref_file, prop.path)
                        ref = False

                key = None

    return prop_map
