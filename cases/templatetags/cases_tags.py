"""Template tags for cases app"""

import json as json_
import os
import re

from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters import HtmlFormatter

from django import template
from django.urls import reverse

from django_import_data.utils import DjangoErrorJSONEncoder

from cases.forms import CaseQuickJumpForm
from utils.constants import NAD27_SRID, NAD83_SRID
from utils.coord_utils import dd_to_dms, coords_to_string
from utils.misc import to_file_link as to_file_link_

register = template.Library()


@register.filter
def safe_json(data):
    """
    Safely JSON-encode an object.
    To protect against XSS attacks, HTML special characters (<, >, &) and unicode newlines
    are replaced by escaped unicode characters. Django does not escape these characters
    by default.
    Output of this method is not marked as HTML safe. If you use it inside an HTML
    attribute, it must be escaped like regular data:
    <div data-user="{{ data|json }}">
    If you use it inside a <script> tag, then the output does not need to be escaped,
    so you can mark it as safe:
    <script>
    var user = {{ data|json|safe }};
    </script>
    Escaped characters taken from Rails json_escape() helper:
    https://github.com/rails/rails/blob/v4.2.5/activesupport/lib/active_support/core_ext/string/output_safety.rb#L60-L113
    """
    unsafe_chars = {
        "&": "\\u0026",
        "<": "\\u003c",
        ">": "\\u003e",
        "\u2028": "\\u2028",
        "\u2029": "\\u2029",
    }
    json_str = json_.dumps(data, cls=DjangoErrorJSONEncoder)

    for (c, d) in unsafe_chars.items():
        json_str = json_str.replace(c, d)

    return json_str


@register.filter
def json(value):
    if not isinstance(value, str):
        value = json_.dumps(value, indent=2, sort_keys=True)

    return highlight(value, JsonLexer(), HtmlFormatter())


@register.filter
def dms(value):
    d, m, s = dd_to_dms(value)
    return f"{d:3d} {m:2d} {s:2.3f}"


@register.inclusion_tag("cases/filter_table.html", takes_context=True)
def filter_table(context, table=None, filter_=None):
    if table is None:
        table = context["table"]
    if filter_ is None:
        filter_ = context["filter"]

    model_name = table.Meta.model._meta.verbose_name.lower()
    model_name_plural = table.Meta.model._meta.verbose_name_plural.lower()
    total_objects = table.Meta.model.objects.count()
    current_objects = len(table.data)
    percent_shown = current_objects / total_objects * 100 if total_objects else 0.0

    return dict(
        request=context["request"],
        table=table,
        filter=filter_,
        model_name_plural=model_name_plural,
        form_id=f"{model_name}-filter-form",
        total_objects=total_objects,
        current_objects=current_objects,
        percent_shown=f"{percent_shown:.2f}%",
    )


def do_format(value):
    return value


@register.inclusion_tag("cases/info_table.html")
def info_table(instance, title, fields):
    rows = [
        (
            instance._meta.get_field(field).verbose_name,
            do_format(getattr(instance, field)),
            # instance._meta.get_field(field).value_to_string(instance),
            instance._meta.get_field(field).help_text,
        )
        if not isinstance(field, tuple)
        else field
        for field in fields
    ]
    return {"title": title, "rows": rows}


@register.inclusion_tag("cases/info_table.html")
def attachment_table(instance, title, fields):
    rows = [
        (
            instance._meta.get_field(field).verbose_name,
            do_format(getattr(instance, field)),
            instance._meta.get_field(field).help_text,
        )
        for field in fields
        if getattr(instance, field)
    ]
    return {"title": title, "rows": rows}


@register.inclusion_tag("cases/info_table.html")
def location_table(instance, title, fields):
    rows = []
    for field in fields:
        if field == "location":
            if instance.location:
                wgs84 = instance.location
                # Need clone in order to create a new object rather than transform in-place
                nad27 = wgs84.transform(NAD27_SRID, clone=True)
                nad83 = wgs84.transform(NAD83_SRID, clone=True)

                url = reverse("facility_kml", args=[str(instance.id)])
                for point in (wgs84, nad83, nad27):
                    point_dms_str = coords_to_string(
                        latitude=point.y, longitude=point.x, concise=True
                    )
                    point_decimal_str = f"{point.y:.8f}, {point.x:.8f}"
                    point_str = f"{point_dms_str} ({point_decimal_str})"
                    if point.srid == instance.original_srs.srid:
                        point_label = f"<b title='SRID: {point.srid}'>{point.srs.name} (original)</b>"
                    elif point.srid == instance.location.srid:
                        point_label = f"<span title='SRID: {point.srid}'>{point.srs.name} (internal)</span>"
                        point_dms_str = f"<a href={url}>{point_dms_str}</a>"
                    else:
                        point_label = (
                            f"<span title='SRID: {point.srid}'> {point.srs.name}</span>"
                        )
                    rows.append((point_label, point_str, ""))
            else:
                rows.append(("Location", None, None))
        else:
            if not isinstance(field, tuple):
                rows.append(
                    (
                        instance._meta.get_field(field).verbose_name,
                        do_format(getattr(instance, field)),
                        instance._meta.get_field(field).help_text,
                    )
                )
            else:
                rows.append(field)
    return {"title": title, "rows": rows}


@register.filter
def basename(value):
    return os.path.basename(value)


@register.filter
def ellipsify(value, numchars):
    str_len = len(value)
    if str_len > numchars:
        return f"… {value[-numchars:]}"
    return value


@register.filter
def trunc_paths(paths):
    prefix = os.path.commonprefix(paths)
    prefix_len = len(prefix)
    ret = []
    if prefix:
        for value in paths:
            prev_slash = value.rfind("/", 0, prefix_len)
            ret.append((value, f"…{value[prev_slash + 1:]}"))
        return ret

    return zip(paths, paths)


@register.filter
def table_model_name(table):
    try:
        try:
            return table._meta.model._meta.verbose_name
        except AttributeError:
            return table._meta.model.__name__
    except AttributeError:
        return None


@register.filter
def table_model_name_plural(table):
    try:
        try:
            return table._meta.model._meta.verbose_name_plural
        except AttributeError:
            return f"{table._meta.model.__name__}s"
    except AttributeError:
        return None


@register.filter
def to_file_link(path):
    return to_file_link_(path)


@register.filter
def view_to_str(view):
    title = view.__class__.__name__

    # If this is a detail view, we use the format "<model_name> <model.__str__()>"
    if "Detail" in title:
        object_ = getattr(view, "object")
        object_as_str = str(object_)
        prefix = object_._meta.verbose_name
        # Avoid repeating text, in edge cases where object.__str__ inserts
        # the model name already
        if prefix not in object_as_str:
            title = f"{prefix} {object_as_str}"
        else:
            title = object_as_str
    # Otherwise, we convert the view class name to a title string
    else:
        # Strip "View" from the end, if it is there
        if title.endswith("View"):
            title = title[: -(len("View"))]

        # Then, convert from CamelCase to Title Case
        # From: https://stackoverflow.com/a/9283563/1883424
        title = re.sub(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))", r" \1", title)

    return title


@register.filter
def request_to_str(request):
    """Convert relative path from request into a title"""

    title = os.path.basename(request.path.strip("/"))
    title = " ".join(x.capitalize() or " " for x in re.split("[-_]", title))

    return title


@register.inclusion_tag("cases/case_quick_jump.html")
def case_quick_jump():
    return {"case_quick_jump_form": CaseQuickJumpForm()}
