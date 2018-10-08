import os

from django import template
import json as _json

from pygments import highlight
from pygments.lexers.data import JsonLexer

from pygments.formatters import HtmlFormatter

register = template.Library()

@register.filter
def filefield_basename(value):
    return os.path.basename(value)

@register.filter
def json(value):
    return highlight(value, JsonLexer(), HtmlFormatter())
