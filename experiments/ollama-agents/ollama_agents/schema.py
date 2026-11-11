"""Validate the explicit JSON-Schema subset used by local agent actions."""

import re

from .errors import AdapterError, infrastructure, invalid

TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict, "array": list, "string": str, "integer": int,
    "number": (int, float), "boolean": bool, "null": type(None),
}
ANNOTATIONS = {"title", "description", "$schema", "$comment", "default", "examples"}
KEYWORDS = {"type", "properties", "required", "additionalProperties", "items", "enum", "const",
            "minProperties", "maxProperties", "minItems", "maxItems", "minLength", "maxLength",
            "minimum", "maximum", "pattern", "anyOf", "oneOf"} | ANNOTATIONS


def check_schema(schema):
    """Reject unsupported schema configuration before any inference starts."""
    if type(schema) is bool:
        return
    if not isinstance(schema, dict) or set(schema) - KEYWORDS:
        raise infrastructure("Unsupported JSON schema or schema keyword")
    _types(schema)
    _definitions(schema)
    _constraints(schema)
    for child in _children(schema):
        check_schema(child)


def validate(value, schema, path="$", *, checked=False):
    """Reject values that violate the configured action schema."""
    if not checked:
        check_schema(schema)
    if type(schema) is bool:
        if not schema:
            raise invalid(f"Schema forbids value at {path}")
        return
    _value_type(value, schema, path)
    _choices(value, schema, path)
    _structure(value, schema, path)
    _bounds(value, schema, path)


def _types(schema):
    """Validate type declarations without accepting arbitrary schema extensions."""
    declaration = schema.get("type", [])
    names = [declaration] if isinstance(declaration, str) else declaration
    if not isinstance(names, list) or any(not isinstance(n, str) or n not in TYPES for n in names):
        raise infrastructure("Invalid schema type declaration")
    if "type" in schema and not names:
        raise infrastructure("Empty schema type declaration")


def _definitions(schema):
    """Validate object and alternative definitions in the supported schema subset."""
    if not isinstance(schema.get("properties", {}), dict):
        raise infrastructure("Schema properties must be an object")
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(n, str) for n in required):
        raise infrastructure("Schema required must be an array of property names")
    for keyword in ("anyOf", "oneOf", "enum"):
        if keyword in schema and (not isinstance(schema[keyword], list) or not schema[keyword]):
            raise infrastructure(f"Schema {keyword} must be a nonempty array")


def _constraints(schema):
    """Validate numeric and pattern constraints in a schema definition."""
    for keyword in ("minProperties", "maxProperties", "minItems", "maxItems", "minLength", "maxLength"):
        if keyword in schema and (type(schema[keyword]) is not int or schema[keyword] < 0):
            raise infrastructure(f"Schema {keyword} must be a nonnegative integer")
    for keyword in ("minimum", "maximum"):
        if keyword in schema and type(schema[keyword]) not in (int, float):
            raise infrastructure(f"Schema {keyword} must be numeric")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except (TypeError, re.error) as error:
            raise infrastructure(f"Invalid schema pattern: {error}") from error


def _children(schema):
    """Enumerate every nested schema, including unused optional properties."""
    children = list(schema.get("properties", {}).values())
    children.extend(schema.get("anyOf", []))
    children.extend(schema.get("oneOf", []))
    for name in ("items", "additionalProperties"):
        if name in schema:
            children.append(schema[name])
    return children


def _value_type(value, schema, path):
    """Apply JSON types while keeping booleans separate from numbers."""
    declaration = schema.get("type")
    names = [declaration] if isinstance(declaration, str) else declaration
    if names is not None and not any(_matches(value, name) for name in names):
        raise invalid(f"Schema type mismatch at {path}: expected {declaration}")


def _matches(value, name):
    """Compare a decoded JSON value with one primitive JSON type."""
    if name in ("integer", "number") and type(value) is bool:
        return False
    if name == "integer" and type(value) is float:
        return value.is_integer()
    return isinstance(value, TYPES[name])


def _choices(value, schema, path):
    """Apply enum, constant and alternative schema constraints."""
    if "const" in schema and not _equal(value, schema["const"]):
        raise invalid(f"Schema const mismatch at {path}")
    if "enum" in schema and not any(_equal(value, item) for item in schema["enum"]):
        raise invalid(f"Schema enum mismatch at {path}")
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = sum(_accepts(value, child, path) for child in schema[keyword])
            if not matches or (keyword == "oneOf" and matches != 1):
                raise invalid(f"Schema {keyword} mismatch at {path}")


def _equal(left, right):
    """Compare JSON values without treating true as the number one."""
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def _accepts(value, schema, path):
    """Observe whether a value matches an already checked alternative."""
    try:
        validate(value, schema, path, checked=True)
    except AdapterError as error:
        if error.status != "invalid_output":
            raise
        return False
    return True


def _structure(value, schema, path):
    """Validate nested properties and array items recursively."""
    if isinstance(value, dict):
        _object(value, schema, path)
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{index}]", checked=True)


def _object(value, schema, path):
    """Validate required and additional object properties."""
    for name in schema.get("required", []):
        if name not in value:
            raise invalid(f"Schema required field {name} missing at {path}")
    properties = schema.get("properties", {})
    extra = schema.get("additionalProperties", True)
    for name, item in value.items():
        validate(item, properties.get(name, extra), f"{path}.{name}", checked=True)


def _bounds(value, schema, path):
    """Apply size, numeric and text constraints to their corresponding JSON types."""
    sizes: dict[type, str] = {dict: "Properties", list: "Items", str: "Length"}
    if type(value) in sizes:
        suffix = sizes[type(value)]
        _range(len(value), schema, "min" + suffix, "max" + suffix, path)
    if type(value) in (int, float):
        _range(value, schema, "minimum", "maximum", path)
    if isinstance(value, str) and "pattern" in schema and re.search(schema["pattern"], value) is None:
        raise invalid(f"Schema pattern mismatch at {path}")


def _range(value, schema, minimum, maximum, path):
    """Apply inclusive schema bounds to a measured value."""
    if minimum in schema and value < schema[minimum]:
        raise invalid(f"Schema {minimum} violation at {path}")
    if maximum in schema and value > schema[maximum]:
        raise invalid(f"Schema {maximum} violation at {path}")
