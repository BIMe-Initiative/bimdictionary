from django import template

from dictionary.models import render_term

register = template.Library()


@register.filter
def highlight_terms(text):
    return render_term(text)

