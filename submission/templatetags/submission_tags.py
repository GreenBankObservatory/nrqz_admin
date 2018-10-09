import os

from django import template
import json as _json

from pygments import highlight
from pygments.lexers.data import JsonLexer

from pygments.formatters import HtmlFormatter

from utils.coord_utils import dd_to_dms

register = template.Library()

@register.filter
def filefield_basename(value):
    return os.path.basename(value)

@register.filter
def json(value):
    return highlight(value, JsonLexer(), HtmlFormatter())

def dms(value):
    d, m, s = dd_to_dms(value)
    return f"{d:3d} {m:2d} {s:2.3f}"
