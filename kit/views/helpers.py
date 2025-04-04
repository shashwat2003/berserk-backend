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
