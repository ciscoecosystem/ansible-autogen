
from utils import render

def gen_go_service(doc):
    class_name = doc.target_class
    generated_module = "{class_name}_service.go".format(class_name=class_name)
    context = doc.terraform_get_context()

    with open(generated_module, 'w') as f:
        mod = render("templates/go_service.go.j2", context)
        f.write(mod)

