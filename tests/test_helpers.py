from schema_viewer.helpers import extract_default, format_description


def test_extract_default():
    assert extract_default("Default value is true") == "true"
    assert extract_default("Default value is true.") == "true"
    assert extract_default("Default value is false") == "false"


def test_format_description():
    assert (
        format_description("see: https://example.com/a?b=#1")
        == 'see: <a href="https://example.com/a?b=#1">https://example.com/a?b=#1</a>'
    )
