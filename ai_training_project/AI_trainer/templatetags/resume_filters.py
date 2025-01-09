from django import template

register = template.Library()


@register.filter
def trim_content(text, max_length=100):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
