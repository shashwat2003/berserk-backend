import re


def recursive_parent_list(instance, field="id", parent="parent"):
    if instance is None:
        return []
    result = recursive_parent_list(getattr(instance, parent), field)
    result.append(getattr(instance, field))
    return result


def recursive_parent_lookup(instance, parent="parent"):
    if instance is None:
        return []
    result = recursive_parent_lookup(getattr(instance, parent), parent)
    result.append(parent)
    return result


def getattr_recursive(instance, field):
    if instance is None:
        return None
    if "." in field:
        field = field.split(".")
        return getattr_recursive(getattr(instance, field[0], None), ".".join(field[1:]))
    return getattr(instance, field, None)


def get_api_from_module_path(module: str):
    """Convert a module path to an API path.
    For example, 'modules.core.api.v1.user' becomes 'v1User'.
    Note: This does not respects url_prefix magic export,
    and is intended to be used only for generic purpose like name generation of response serializer.
    """

    match = re.search(r"\.api\.(.+)$", module)
    if match:
        (path,) = match.groups()
        parts = path.split(".")
        return "".join(p.capitalize() for p in parts)
    return module.replace(".", "").capitalize()
