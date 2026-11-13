# Copyright 2017-2018 Simone Orsi
# Copyright 2026 Camptocamp SA
# @author Akim Juillerat <akim.juillerat@camptocamp.com>
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


# Borrowed from `connector_algolia.utils` (OCA/search-engine), itself
# borrowed from `cms_form.utils`. Changes: the TypeError is chained to the
# original one (B904), and a long line is split.
def data_merge(left_value, right_value):
    """Merges `right_value` into `left_value` and return merged result.

    NOTE: tuples and arbitrary objects are not handled
    as it is totally ambiguous what should happen.
    Thanks to http://stackoverflow.com/a/15836901/647924
    """
    key = None
    try:
        if left_value is None or isinstance(left_value, (str, int, float)):
            # border case for first run or if left_value is a primitive
            left_value = right_value
        elif isinstance(left_value, list):
            # lists can be only appended
            if isinstance(right_value, list):
                # merge lists
                left_value.extend(right_value)
            else:
                # append to list
                left_value.append(right_value)
        elif isinstance(left_value, dict):
            # dicts must be merged
            if isinstance(right_value, dict):
                for key in right_value:
                    if key in left_value:
                        left_value[key] = data_merge(left_value[key], right_value[key])
                    else:
                        left_value[key] = right_value[key]
            else:
                raise ValueError(
                    f'Cannot merge non-dict "{right_value}" into dict "{left_value}"'
                )
        else:
            raise NotImplementedError(
                f'NOT IMPLEMENTED "{right_value}" into "{left_value}"'
            )
    except TypeError as type_error:  # pragma: no cover
        raise TypeError(
            f'"{type_error}" in key "{key}" '
            f'when merging "{right_value}" into "{left_value}"'
        ) from type_error
    return left_value
