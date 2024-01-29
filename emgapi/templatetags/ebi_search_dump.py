from django import template

register = template.Library()


@register.simple_tag
def xml_safe(unsafe_string: str):
    if not unsafe_string:
        return None

    replacements = str.maketrans({
        "<": "&lt;",
        ">": "&gt;",
        "&": "&amp;",
        "'": "&apos;",
        '"': "&quot;",
    })

    return unsafe_string.translate(replacements)
