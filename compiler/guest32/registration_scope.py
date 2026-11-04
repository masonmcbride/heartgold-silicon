"""Keep source-reviewed callback registration metadata with its owner.

Other image plans have no reviewed registration specification yet.
Do not borrow OVY_0's edges or infer that unreviewed callbacks are safe.
"""

REVIEWED = frozenset(("OVY_0", "OVY_38"))


def scoped_spec(owner, spec):
    if owner in REVIEWED:
        return spec

    def empty(value):
        if isinstance(value, dict):
            return {key: empty(item) for key, item in value.items()}
        if isinstance(value, list):
            return []
        return value

    return empty(spec)
