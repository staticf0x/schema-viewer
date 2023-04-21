from pathlib import Path

from schema_viewer.loader import Loader
from schema_viewer.property import Property

ROOT = Path(__file__).parent / "fixtures"


def test_basic():
    loader = Loader(str(ROOT / "test.yaml"), str(ROOT / "test.yaml"))
    res = loader.load_properties()

    root = Property(name="test", type="object", description="Test object")

    expected = [
        root,
        Property(name="name", type="string", description="Name of the object", parent=root),
    ]

    assert res == expected
