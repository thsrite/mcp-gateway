import re

NAMESPACE_SEPARATOR = "__"


def add_namespace(namespace: str, name: str) -> str:
    return f"{namespace}{NAMESPACE_SEPARATOR}{name}"


def parse_namespace(namespaced_name: str) -> tuple[str, str]:
    parts = namespaced_name.split(NAMESPACE_SEPARATOR, 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid namespaced name: {namespaced_name}")
    return parts[0], parts[1]


def sanitize_namespace(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized.strip("_").lower()
