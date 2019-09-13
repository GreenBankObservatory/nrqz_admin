def to_file_link(path):
    # If path starts with a \, assume that it is a network path
    # (e.g. \\gbfiler). These paths must be prefixed with extra backslashes in
    # order to function properly
    if path.startswith(r"\\"):
        return f"file://///{path[2:]}"

    # If path starts with http, treat it as a web link and make no changes
    # to it
    if path.lower().startswith("http"):
        return path

    return f"file://{path}"
