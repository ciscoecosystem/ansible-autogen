
from utils import render, snakify
from ansible_generator import get_context
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword
from utils import PREFIX
import os.path as p
import sys
import posixpath

ignore_set = set(["descr","lcOwn","name","ownerKey", "ownerTag", "pcTag", "uid"])


def get_terraform_context(mim, mo):
    context = get_context(mim, mo, "terraform")
    doc = context["doc"]
    all_parameters = context["keys"]
    p_all_parameters = context["pkeys"]

    doc["slug_label"] = doc["label"].replace(" ","")
    all_parameters = {k: v for k, v in all_parameters.items() if k not in ignore_set}
    p_all_parameters = {k: v for k, v in p_all_parameters.items() if k not in ignore_set}
    context["doc"] = doc 
    context["keys"] = all_parameters
    context["pkeys"] = p_all_parameters
    print(context["hierarchy"])
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
                mod = render(posixpath.join(PREFIX,'go_service.go.j2'), context)
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


def gen_go_module(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating module for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "{}.go".format(snakify(klass))

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
                mod = render(posixpath.join(PREFIX,'go_module.go.j2'), context)
                f.write(mod)
        except ModuleGenerationException as e:
            print(e,file=sys.stderr)
        print("Successfully created module for {0}".format(klass))

    return lines

def gen_terraform_resource(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating resource for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "resource_aci_{}.go".format(klass.lower())

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
                mod = render(posixpath.join(PREFIX,'resource.go.j2'), context)
                f.write(mod)
        except ModuleGenerationException as e:
            print(e,file=sys.stderr)
        print("Successfully created resource for {0}".format(klass))

    return lines

def gen_terraform_rdocs(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating rdocs for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "resource_aci_{}.html.markdown".format(klass.lower())

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
                mod = render(posixpath.join(PREFIX,'rdocs.html.markdown.j2'), context)
                f.write(mod)
        except ModuleGenerationException as e:
            print(e,file=sys.stderr)
        print("Successfully created rdocs for {0}".format(klass))

    return lines

def gen_terraform_acceptance_test(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating acc tests for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "resource_aci_{}_test.go".format(klass.lower())

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
                mod = render(posixpath.join(PREFIX,'acceptance_test.go.j2'), context)
                f.write(mod)
        except ModuleGenerationException as e:
            print(e,file=sys.stderr)
        print("Successfully created acceptance tests for {0}".format(klass))

    return lines
    