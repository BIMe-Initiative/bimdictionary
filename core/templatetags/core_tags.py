from django import template
from django.utils.safestring import mark_safe

from core.models import TextBlock

register = template.Library()


@register.simple_tag()
def textblock(slug):
    block, created = TextBlock.objects.get_or_create(slug=slug)
    return mark_safe(block.text)


