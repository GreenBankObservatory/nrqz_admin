import os

from django import template

from utils.numrange import get_str_from_nums


register = template.Library()


@register.filter
def range_notation(value):
    return get_str_from_nums(value)


@register.filter
def basename(value):
    return os.path.basename(value)
