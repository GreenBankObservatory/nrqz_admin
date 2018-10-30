def discover_fields(layout):
    """Discover all fields defined in a layout object

    This is used to avoid defining the field list in two places --
    the layout object is instead inspected to determine the list
    """

    fields = []
    try:
        comps = list(layout)
    except TypeError:
        return fields
    for comp in comps:
        if isinstance(comp, str):
            fields.append(comp)
        else:
            fields.extend(discover_fields(comp))

    return fields
