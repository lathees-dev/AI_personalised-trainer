from django import template

register = template.Library()

@register.simple_tag
def get_score_percentage(correct, total):
    if total == 0:
        return 0
    return int((correct / total) * 100)

@register.filter
def percentage(value):
    return f"{value}%"

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary using bracket notation"""
    return dictionary.get(key, '') 