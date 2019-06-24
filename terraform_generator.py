
from utils import render, snakify
from ansible_generator import get_context
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword
from utils import PREFIX
import os.path as p
import sys
import posixpath
import re


ignore_set = set(["descr","lcOwn","name","ownerKey", "ownerTag", "pcTag", "uid"])


def get_terraform_context(mim, mo):
    context = get_context(mim, mo, "terraform")
    doc = context["doc"]
    all_parameters = context["keys"]
    p_all_parameters = context["pkeys"]
    st = re.sub('[^A-Za-z0-9]+','',doc["label"])
    doc["slug_label"] = st
    all_parameters = {k: v for k, v in all_parameters.items() if k not in ignore_set}
    p_all_parameters = {k: v for k, v in p_all_parameters.items() if k not in ignore_set}

    context["doc"] = doc 
    context["keys"] = all_parameters
    context["pkeys"] = p_all_parameters
    return context

def gen_go_service(klass, value,context):
    lines  = [] # lines for class list text file

    print("Creating service for {0}".format(klass))
    out = "{}_service.go".format(klass)

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


def gen_go_module(klass, value,context):
    lines  = [] # lines for class list text file

    print("Creating module for {0}".format(klass))
    out = "{}.go".format(snakify(klass))

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

def gen_terraform_resource(klass, value,context):

    lines  = [] # lines for class list text file

    print("Creating resource for {0}".format(klass))
    out = "resource_aci_{}.go".format(klass.lower())

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

def gen_terraform_rdocs(klass, value,context):

    lines  = [] # lines for class list text file

    print("Creating rdocs for {0}".format(klass))
    out = "{}.html.markdown".format(klass.lower())

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

def gen_terraform_acceptance_test(klass, value,context):

    lines  = [] # lines for class list text file

    print("Creating acc tests for {0}".format(klass))
    out = "resource_aci_{}_test.go".format(klass.lower())

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

def gen_terraform_data_source(klass, value,context):

    lines  = [] # lines for class list text file

    print("Creating data source  for {0}".format(klass))
    out = "data_source_aci_{}.go".format(klass.lower())

    context['filename'] = out
    lines.append("{} {}".format(klass, context['dn']))
    try:
        with open(out, 'w') as f:
            mod = render(posixpath.join(PREFIX,'datasource.go.j2'), context)
            f.write(mod)
    except ModuleGenerationException as e:
        print(e,file=sys.stderr)
    print("Successfully created data source for {0}".format(klass))

    return lines

def gen_terraform_data_source_docs(klass, value,context):

    lines  = [] # lines for class list text file

    print("Creating data source docs for {0}".format(klass))
    out = "data_source_{}.html.markdown".format(klass.lower())

    context['filename'] = out
    lines.append("{} {}".format(klass, context['dn']))
    try:
        with open(out, 'w') as f:
            mod = render(posixpath.join(PREFIX,'datasource_docs.html.markdown.j2'), context)
            f.write(mod)
    except ModuleGenerationException as e:
        print(e,file=sys.stderr)
    print("Successfully created data source docs for {0}".format(klass))

    return lines
    