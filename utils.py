from jinja2 import Environment, FileSystemLoader


# this is similar to capitalize, just that this doesnt lower case everything else
def capital(value):
    return value[0].upper() + value[1:]

def render(template_name, context):
    env = Environment(loader=FileSystemLoader('.'))
    env.filters["capital"] = capital
    return env.get_template(template_name).render(context)
