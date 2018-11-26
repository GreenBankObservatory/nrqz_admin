"""Template tags for cases app"""

from django import template

from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters import HtmlFormatter

from utils.coord_utils import dd_to_dms


register = template.Library()


@register.filter
def json(value):
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
        )
        for field in fields
        if getattr(instance, field)
    ]
    return {"title": title, "rows": rows}


@register.inclusion_tag("cases/info_table.html")
def location_table(instance, title, fields):
    fields.remove("latitude")
    latitude = getattr(instance, "latitude")
    latitude_str = instance._meta.get_field("latitude").value_to_string(instance)
    fields.remove("longitude")
    longitude = getattr(instance, "longitude")
    longitude_str = instance._meta.get_field("longitude").value_to_string(instance)
    url = f"https://www.google.com/maps/place/{latitude},{longitude}"
    rows = [("Coordinates", f"<a href={url}>({latitude_str}, {longitude_str})</a>")]

    rows.extend(
        [
            (
                instance._meta.get_field(field).verbose_name,
                instance._meta.get_field(field).value_to_string(instance),
            )
            for field in fields
        ]
    )
    return {"title": title, "rows": rows}


@register.simple_tag
def get_verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name
