def to_file_link(path):
    if path.startswith(r"\\"):
        return f"file://///{path[2:]}"
    return f"file://{path}"
