#encoding=UTF-8
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def uservoice_client_key():
    return settings.USERVOICE_CLIENT_KEY