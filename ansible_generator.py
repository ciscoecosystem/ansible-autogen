#!/usr/bin/env python3

import argparse
import sys
import logging
import re
import json
import os
import os.path as p
from jinja2 import Environment, FileSystemLoader
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword
from utils import PREFIX, render,snakify


not_allowed = ['type','id']

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

        delimiters = r"(\{\[|\{).*?(\]\}|\})" #pattern to remove paramter names
        replace = r"\g<1>\g<2>"
        flip_brackets = r"(\{\[).*?(\]\})" #pattern to sub {[]} to [{}]

        rn_format = re.sub(delimiters, replace, rn_format)
        rn_format = re.sub(flip_brackets, "[{}]", rn_format)

        # extra operation if needed
        if kind == "terraform":
            replace_brases = lambda rn: re.sub("{}","%s", rn)
            rn_format = replace_brases(rn_format)

        # get variable names
        label = klass_mo.label.lower().replace(" ", "_") if klass_mo.label else (klass_mo.name.replace(":","")).replace("'","")
        label = label.replace("'","")
        if kind == "terraform":
            args = {}
            for prop in props:
                if klass != target:
                    # import pdb; pdb.set_trace()
                    details = { 'options': klass_mo.properties[prop]['options'],
                                'naming': True,
                                'help': klass_mo.properties[prop]['help']}
                    var = label if prop == "name" else "{0}_{1}".format(label, prop)
                    if var in not_allowed:
                        args["{0}_{1}".format(label,var)] = var
                    else:
                        args[var] = var
                    details['var'] = var
                    all_parameters[var] = details
                else:
                    all_parameters[prop]['naming'] = True
                    if all_parameters[prop]['var'] in not_allowed:
                        args["{0}_{1}".format(label,all_parameters[prop]['var'])] = all_parameters[prop]['var']
                    else:
                        args[all_parameters[prop]['var']] = all_parameters[prop]['var']
        else:
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
                args = {}
            label_str = (klass_mo.label.replace(" ","")).replace("'","") if klass_mo.label else (klass_mo.name.replace(":","")).replace("'","")
            label_str = label_str[0].upper() + label_str[1:]
            hierarchy.append({'name': klass,
                            'args': args,
                            'rn': rn_format,
                            'label': label_str,
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
    return hierarchy

def get_ansible_context(mim, mo):
    return get_context(mim, mo, "ansible")


def get_context(mim, mo, kind):

    all_parameters = {} # will add other class naming later
    ro_params = {}
    for key, value in mo.properties.items():
        details = {'options': value['options'], #TODO: make sure options for is a list, not dict
            # 'options': list(value['options'].keys()),
            # 'label': value['label'],
            'help': value['help'],
            'payload': key,
            'var': '_' + key if iskeyword(key) else key,
            'isConfigurable': value['isConfigurable']}
        if key == 'name':
            details['aliases'] = [mo.label.lower().replace(" ", "_")]
        if value['isConfigurable']:
            all_parameters[key] = details
        else:
            ro_params[key] = details

    label_str = mo.label.replace("'","") if mo.label else (mo.name.replace(":","")).replace("'","")
    label_str = label_str[0].upper() + label_str[1:]
    attributes = {'label': label_str,
                    'deletable': mo.isDeletable,
                    'description': mo.help,
                    'name': mo.name,
                    'abstract': mo.isAbstract,
                    'configurable': mo.isConfigurable,
                    'isRelation': mo.isRelation,
                    'identifiedBy': mo.identifiedBy}

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
            if key in not_allowed:
                payload_parameters["{0}_{1}".format(label_str.replace(" ",""),key)] = value
            else:
                payload_parameters[key] = value
    ro_parameteres = {}

    for key, value in ro_params.items():
        if "payload" in value:
            if key in not_allowed:
                ro_parameteres["{0}_{1}".format(label_str.replace(" ",""),key)] = value
            else:
                ro_parameteres[key] = value
    context = {'class': mo.klass,
            'keys': all_parameters,
            'pkeys': payload_parameters,
            'rokeys': ro_parameteres,
            'hierarchy': hierarchy,
            'doc': attributes,
            'dn': mo.dnFormat[choice][0]}
    relContext = {}
    for relation in mo.relationTo:
        relation_context = get_context(mim,mim.get_class(relation["relation"]),kind)
        relation_context["relToClass"] = relation["class"]
        relation_context["cardinality"] = relation["cardinality"]
        relContext[relation["relation"]] = relation_context
    
    context["relationTo"] = relContext
    return context

def apply_ansible_filter(context):
    mappings = {}
    with open(f"{os.getcwd()}/ansible_mappings.json") as f:
        mappings = json.load(f)
    
    current_class = mappings.get('classes').get(context['class'])
    if current_class:
        if current_class.get('filename'):
            context['filename'] = current_class.get('filename')
        for key, value in current_class.get('keys',{}).items():
            allowed_key = key
            if key in context['keys'].keys():
                context['keys'][key]['human_name'] = value
            if key in not_allowed:
                allowed_key = "{0}_{1}".format(context['doc']['label'].replace(" ",""),key)
            if allowed_key in context['pkeys'].keys():
                context['pkeys'][allowed_key]['human_name'] = value 
        for key, value  in current_class.get("relations", {}).items():
            if key in context['relationTo'].keys():
                context['relationTo'][key]['human_name'] = value  
        if current_class.get('label'):
            context['doc']['label'] = current_class.get('label')
        return context
    else:
        # class is not there in the mappings, ignore filtering.
        return context

def gen_ansible_module(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        print("Creating module for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "aci_{}.py".format(klass)

        if value.isAbstract: # use abstract template
            context = {'klass': klass, 'name': value.name, 'label': value.label, 'description': value.help, 'filename': out}
            mod = render(p.join(PREFIX,'ansible_2.6_read_only.py.j2'), context)
            with open(out, 'w') as f:
                f.write(mod)
        else:
            context = get_ansible_context(mim, value)
            context['filename'] = out
            context = apply_ansible_filter(context)
            print(json.dumps(context))
            lines.append("{} {}".format(klass, context['dn']))
            try:
                with open(context['filename'], 'w') as f:
                    mod = render(p.join(PREFIX,'ansible_2.6_read_write.py.j2'), context)
                    f.write(mod)
            except ModuleGenerationException as e:
                print(e, file=sys.stderr)
        print("Successfully created module for {0}".format(klass))

    return lines
