
from utils import render, snakify

def gen_go_service(doc):
    class_name = doc.target_class
    generated_module = "{class_name}_service.go".format(class_name=class_name)
    context = doc.terraform_get_context()

    with open(generated_module, 'w') as f:
        mod = render("templates/go_service.go.j2", context)
        f.write(mod)


def gen_go_module(doc):
    class_name = doc.target_class
    generated_module = "{class_name}.go".format(class_name=class_name)
    context = doc.terraform_get_context()

    with open(generated_module, 'w') as f:
        mod = render("templates/go_module.go.j2", context)
        f.write(mod)

def gen_terraform_resource(doc):
    class_name = doc.target_class
    generated_module = "resource_{class_name}.go".format(class_name=snakify(class_name))
    context = doc.terraform_get_context()

    with open(generated_module, 'w') as f:
        mod = render("templates/resource.go.j2", context)
        f.write(mod)