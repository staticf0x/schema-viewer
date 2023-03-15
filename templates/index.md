# Product Version Schema

{% for prop in properties %}
## {{ prop.name }}

{% if prop.deprecated %}<span style="color: red;">Deprecated</span><br>{% endif %}

<small>Path: {{ prop.path }}</small><br>

**Type**: {{ prop.type }}<br>
{% if prop.description %}**Description**: {{ prop.description }}<br>{% endif %}{% if prop.default %}**Default value**: {{ prop.default }}<br>{% endif %}{% if prop.example %}**Example value**: {{ prop.example }}<br>{% endif %}{% if prop.pattern %}**Pattern**: {{ prop.pattern }}<br>{% endif %}{% if prop.min_items %}**Min items**: {{ prop.min_items }}<br>{% endif %}{% if prop.max_items %}**Max items**: {{ prop.max_items }}<br>{% endif %}{% if prop.enum %}**Possible values**:
{% for val in prop.enum %}
- {{ val }}{% endfor %}
{% endif %}

{% endfor %}