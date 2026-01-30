from django import template

register = template.Library()


@register.filter
def get_item(form, key):
    try:
        return form[key]
    except Exception:
        return None
