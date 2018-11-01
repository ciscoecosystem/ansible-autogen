#!/usr/bin/env python3

import argparse
import sys
import logging
import re
import os.path as p
from jinja2 import Environment, FileSystemLoader
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword
from utils import PREFIX, render



def set_hierarchy(all_parameters, classes, mim, target, kind="ansible"):
    """add parent class naming to ansible parameters and return hierarchy dict"""
    hierarchy = []
    unnamed_rn = ""

    for klass in classes:
        klass_mo = mim.get_class(klass)
        props = klass_mo.identifiedBy
        if len(props) == 0 and klass != target:
            if klass != "polUni":
                unnamed_rn += klass_mo.rnFormat + "/"
            continue
        rn_format = unnamed_rn + klass_mo.rnFormat
        unnamed_rn = ""

        delimiters = "(\{\[|\{).*?(\]\}|\})" #pattern to remove paramter names
        replace = "\g<1>\g<2>"
        flip_brackets = "(\{\[).*?(\]\})" #pattern to sub {[]} to [{}]

        rn_format = re.sub(delimiters, replace, rn_format)
        rn_format = re.sub(flip_brackets, "[{}]", rn_format)

        # extra operation if needed
        if kind == "terraform":
            replace_brases = lambda rn: re.sub("{}","%s", rn)
            rn_format = replace_brases(rn_format)

        # get variable names
        label = klass_mo.label.lower().replace(" ", "_")
        args = []
        for prop in props:
            if klass != target:
                # import pdb; pdb.set_trace()
                details = { 'options': klass_mo.properties[prop]['options'],
                            'naming': True,
                            'help': klass_mo.properties[prop]['help']}
                var = label if prop == "name" else "{0}_{1}".format(label, prop)
                args.append(var)
                details['var'] = var
                all_parameters[var] = details
            else:
                all_parameters[prop]['naming'] = True
                args.append(all_parameters[prop]['var'])
        
        if kind == "terraform":
            if len(args) == 0:
                args = [None]
            hierarchy.append({'name': klass,
                            'args': args,
                            'rn': rn_format,
                            'label': klass_mo.label.replace(" ","")
                            })
        else:
        # contruct rn format string
            if len(args) != 0:
                arg_str = "("
                i = 0
                while i < len(args) - 1:
                    arg_str += args[i] + ", "
                    i += 1
                arg_str += args[-1] + ")"
            else:
                arg_str = "()"
            rn =  "\'{0}\'.format{1}".format(rn_format, arg_str)

            #contruct filter string
            if len(args) == 0:
                filter_str = ""
            elif len(args) == 1:
                filter_str = "\'eq({0}.{1}, \"{{}}\")\'.format({2})".format(klass, props[0], args[0])
            else:
                filter_str = "\'and("
                i = 0
                while i < len(args) - 1:
                    filter_str += "eq({0}.{1}, \"{{}}\"),".format(klass, props[i])
                    i += 1
                filter_str += "eq({0}.{1}, \"{{}}\"))\'.format{2}".format(klass, props[i], arg_str)

            if filter_str == "":
                filter_str = "\'\'"
            if len(args) == 0:
                args = [None]

            hierarchy.append({'name': klass,
                            'args': args,
                            'rn': rn,
                            'filter': filter_str
                            })
    print(hierarchy)
    return hierarchy

def get_ansible_context(mim, mo):
    return get_context(mim, mo, "ansible")


def get_context(mim, mo, kind):

    all_parameters = {} # will add other class naming later
    for key, value in mo.properties.items():
        if value['isConfigurable']:
            details = {'options': value['options'], #TODO: make sure options for is a list, not dict
                        # 'options': list(value['options'].keys()),
                        # 'label': value['label'],
                        'help': value['help'],
                        'payload': key,
                        'var': '_' + key if iskeyword(key) else key,
                        'isConfigurable': value['isConfigurable']}
            if key == 'name':
                details['aliases'] = [mo.label.lower().replace(" ", "_")]
            all_parameters[key] = details

    attributes = {'label': mo.label,
                    'deletable': mo.isDeletable,
                    'description': mo.help,
                    'name': mo.name,
                    'abstract': mo.isAbstract,
                    'configurable': mo.isConfigurable,
                    'isRelation': mo.isRelation}

    # ask user to choose DN format
    if len(mo.dnFormat) > 1:
        i = 1
        for format in mo.dnFormat:
            print("{}: {}".format(i, format[0]))
            i += 1
        choice = int(input("Enter number corresponding to desired DN format for {}\n".format(mo.klass)))-1
    elif len(mo.dnFormat) == 0:
        raise ModuleGenerationException("no DNs")
    else:
        choice = 0

    classes = mo.dnFormat[choice][1]

    hierarchy = None
    hierarchy = set_hierarchy(all_parameters, classes, mim, mo.klass, kind=kind)

    payload_parameters = {} #target class properties only #TODO just copy all parameters first
    for key, value in all_parameters.items():
        if "payload" in value:
            payload_parameters[key] = value

    context = {'class': mo.klass,
            'keys': all_parameters,
            'pkeys': payload_parameters,
            'hierarchy': hierarchy,
            'doc': attributes,
            'dn': mo.dnFormat[choice][0]}
    # print(context)
    return context


def gen_ansible_module(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating module for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "auto_{}.py".format(klass)

        if value.isAbstract: # use abstract template
            context = {'klass': klass, 'name': value.name, 'label': value.label, 'description': value.help, 'filename': out}
            mod = render(p.join(PREFIX,'ansible_2.6_read_only.py.j2'), context)
            with open(out, 'w') as f:
                f.write(mod)
        else:
            context = get_ansible_context(mim, value)
            context['filename'] = out
            lines.append("{} {}".format(klass, context['dn']))
            try:
                with open(out, 'w') as f:
                    mod = render(p.join(PREFIX,'ansible_2.6_read_write.py.j2'), context)
                    f.write(mod)
            except ModuleGenerationException as e:
                print(e, file=sys.stderr)
        print("Successfully created module for {0}".format(klass))

    return lines
