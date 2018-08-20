from jinja2 import Environment, FileSystemLoader
import re

PREFIX = "templates"



# this is similar to capitalize, just that this doesnt lower case everything else
def capital(value):
    return value[0].upper() + value[1:]

def snakify(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def render(template_name, context):
    env = Environment(loader=FileSystemLoader('.'))
    env.filters["capital"] = capital
    env.filters["snakify"] = snakify
    return env.get_template(template_name).render(context)
