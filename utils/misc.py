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


# Adapted from https://stackoverflow.com/a/9756239/11870070
def put_help_text_in_title(cls):
    init = cls.__init__

    def __init__(self, *args, **kwargs):
        init(self, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["title"] = field.help_text
            field.help_text = None

    cls.__init__ = __init__
    return cls
