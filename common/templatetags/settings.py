from django import template
from django.conf import settings as django_settings

register = template.Library()


@register.simple_tag
def settings(name):
    return getattr(django_settings, name)
