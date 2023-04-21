"""Class representing a jsonschema property."""
from dataclasses import dataclass, field


@dataclass
class Property:
    """Class representing a jsonschema property."""

    name: str
    type: str
    deprecated: bool = False
    description: str = ""
    default: str = ""
    example: str = ""
    properties: list = field(default_factory=list)
    parent: object = None
    min_items: int = 0
    max_items: int = 0
    enum: list = field(default_factory=list)
    required: bool = False
    pattern: str = ""
    option: int = 0
    condition: str = ""

    def nest_level(self) -> int:
        """Return an integer with how nested the property is."""
        p = self
        level = 0

        while p.parent:
            level += 1
            p = p.parent

        return level

    @property
    def path(self) -> str:
        """Return a human-friendly path to the property."""
        parts = []
        p = self

        while p.parent:
            parts.append(p.name)
            p = p.parent

        parts.append(p.name)

        return " » ".join(parts[::-1])
