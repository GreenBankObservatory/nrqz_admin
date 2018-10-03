import os

from django import template

register = template.Library()

@register.filter
def filefield_basename(value):
    return os.path.basename(value)
