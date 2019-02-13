"""Template tags for cases app"""

import json as json_
import os

from django_import_data.models import DjangoErrorJSONEncoder

from django.urls import reverse
from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters import HtmlFormatter

from utils.coord_utils import dd_to_dms, coords_to_string

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


@register.inclusion_tag("cases/info_table.html")
def info_table(instance, title, fields):
    rows = [
        (
            instance._meta.get_field(field).verbose_name,
            instance._meta.get_field(field).value_to_string(instance),
            instance._meta.get_field(field).help_text,
        )
        for field in fields
    ]
    return {"title": title, "rows": rows}


@register.inclusion_tag("cases/info_table.html")
def attachment_table(instance, title, fields):
    rows = [
        (
            instance._meta.get_field(field).verbose_name,
            instance._meta.get_field(field).value_to_string(instance),
            instance._meta.get_field(field).help_text,
        )
        for field in fields
        if getattr(instance, field)
    ]
    return {"title": title, "rows": rows}


@register.inclusion_tag("cases/info_table.html")
def location_table(instance, title, fields):
    if "location" not in fields:
        return {}
    fields.remove("location")
    longitude, latitude = instance.location.coords
    location_str = coords_to_string(latitude, longitude, concise=True)

    url = reverse("facility_kml", args=[str(instance.id)])
    rows = [("Coordinates", f"<a href={url}>{location_str}</a>", "")]

    rows.extend(
        [
            (
                instance._meta.get_field(field).verbose_name,
                instance._meta.get_field(field).value_to_string(instance),
                instance._meta.get_field(field).help_text,
            )
            for field in fields
        ]
    )
    return {"title": title, "rows": rows}


@register.filter
def basename(value):
    return os.path.basename(value)
