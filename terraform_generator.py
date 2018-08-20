
from utils import render, snakify
from ansible_generator import get_ansible_context
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword
from utils import PREFIX
import os.path as p
import sys

ignore_set = set(["descr","lcOwn","name","ownerKey", "ownerTag", "pcTag", "uid"])


def get_terraform_context(mim, mo):
    context = get_ansible_context(mim, mo)
    doc = context["doc"]
    all_parameters = context["keys"]

    doc["slug_label"] = doc["label"].replace(" ","")
    all_parameters = {k: v for k, v in all_parameters.items() if k not in ignore_set}
    
    context["doc"] = doc 
    context["keys"] = all_parameters
    return context

def gen_go_service(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating service for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "{}_service.go".format(klass)

        # if value.isAbstract: # use abstract template
        #     context = {'klass': klass, 'name': value.name, 'label': value.label, 'description': value.help, 'filename': out}
        #     mod = render(p.join(PREFIX,'ansible_2.6_read_only.py.j2'), context)
        #     with open(out, 'w') as f:
        #         f.write(mod)
        # else:
        context = get_terraform_context(mim, value)
        context['filename'] = out
        lines.append("{} {}".format(klass, context['dn']))
        try:
            with open(out, 'w') as f:
                mod = render(p.join(PREFIX,'go_service.go.j2'), context)
                f.write(mod)
        except ModuleGenerationException as e:
            print(e,file=sys.stderr)
        print("Successfully created module for {0}".format(klass))

    return lines



# def gen_go_service(doc):
#     class_name = doc.target_class
#     generated_module = "{class_name}_service.go".format(class_name=class_name)
#     context = doc.terraform_get_context()

#     with open(generated_module, 'w') as f:
#         mod = render("templates/go_service.go.j2", context)
#         f.write(mod)


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