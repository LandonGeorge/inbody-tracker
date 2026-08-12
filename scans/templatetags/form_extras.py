from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    """Render a bound field with an extra CSS class, e.g. for Bootstrap's form-control."""
    classes = f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()
    if field.errors:
        classes += " is-invalid"
    return field.as_widget(attrs={"class": classes})
