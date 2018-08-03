from jinja2 import Environment, FileSystemLoader


def render(template_name, context):
    env = Environment(loader=FileSystemLoader('.'))
    return env.get_template(template_name).render(context)
