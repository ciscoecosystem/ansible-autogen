#!/usr/bin/env python3

import argparse
import sys
import logging
import re
from jinja2 import Environment, FileSystemLoader
from object_model import MIM, ModuleGenerationException
from keyword import iskeyword

# def gen_ansible_module(doc):
#     class_name = doc.target_class
#     generated_module = "generated_{class_name}_module.py".format(class_name=class_name)
#     context = doc.ansible_get_context()
#     extra_context = { 
#                 'deletable': doc.attributes["deletable"],
#                 'filename': generated_module
#             }
#     context.update(extra_context)

    
#     with open(generated_module, 'w') as f:
#         mod = render('templates/ansible_module.py.j2', context)
#         f.write(mod)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

        def flush(self):
            for handler in self.logger.handlers:
                handler.flush()

# Replace stdout with logging to file at INFO level
# sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)
# ------------------------------------------------------------------------------------

def render(template_name, context):
    env = Environment(loader=FileSystemLoader('.'))
    return env.get_template(template_name).render(context)


def set_hierarchy(all_parameters, classes, mim, target):
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

        # get variable names
        label = klass_mo.label.lower().replace(" ", "_")
        args = []
        for prop in props:
            if klass != target:
                details = {'label': klass_mo.properties[prop]['label'],
                            'naming': True,
                            'help': klass_mo.properties[prop]['help']}
                var = label if prop == "name" else "{0}_{1}".format(label, prop)
                args.append(var)
                details['var'] = var
                all_parameters[var] = details
            else:
                all_parameters[prop]['naming'] = True
                args.append(all_parameters[prop]['var'])

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

    all_parameters = {} # will add other class naming later
    for key, value in mo.properties.items():
        if value['isConfigurable']:
            details = {'options': value['options'], #TODO: make sure options for is a list, not dict
                        # 'options': list(value['options'].keys()),
                        # 'label': value['label'],
                        'help': value['help'],
                        'payload': key,
                        'var': '_' + key if iskeyword(key) else key}
            if key == 'name':
                details['aliases'] = [mo.label.lower().replace(" ", "_")]
            all_parameters[key] = details

    attributes = {'label': mo.label,
                    'deletable': mo.isDeletable,
                    'description': mo.help,
                    'name': mo.name,
                    'abstract': mo.isAbstract,
                    'configurable': mo.isConfigurable}

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
    hierarchy = set_hierarchy(all_parameters, classes, mim, mo.klass)

    payload_parameters = {} #target class properties only #TODO just copy all parameters first
    for key, value in all_parameters.items():
        if "payload" in value:
            payload_parameters[key] = value

    return {'class': mo.klass,
            'keys': all_parameters,
            'pkeys': payload_parameters,
            'hierarchy': hierarchy,
            'doc': attributes,
            'dn': mo.dnFormat[choice][0]}


def ansible_model(classes, meta):
    mim = MIM(meta)
    model = {klass: mim.get_class(klass) for klass in classes}
    lines  = [] # lines for class list text file

    for klass, value in model.items():
        logger.info("Creating module for {0}".format(klass))
        # out = "generated_{0}_module.py".format(klass)
        out = "auto_{}.py".format(klass)

        if value.isAbstract: # use abstract template
            context = {'klass': klass, 'name': value.name, 'label': value.label, 'description': value.help, 'filename': out}
            mod = render('ansible_2.6_read_only.py.j2', context)
            with open(out, 'w') as f:
                f.write(mod)
        else:
            context = get_ansible_context(mim, value)
            context['filename'] = out
            lines.append("{} {}".format(klass, context['dn']))
            try:
                with open(out, 'w') as f:
                    mod = render('ansible_2.6_read_write.py.j2', context)
                    f.write(mod)
            except ModuleGenerationException as e:
                logger.error(e)
        logger.info("Successfully created module for {0}".format(klass))

    return lines


def main():
    #TODO: add arguments for other documentation sources
    parser = argparse.ArgumentParser(description='Create an Ansible Module for a specified ACI class')
    parser.add_argument('-c', '--class', help='name of the class that the output module will manipulate', dest='klass')
    parser.add_argument('-l', '--list', help='path of text file containing class names')
    parser.add_argument('-m', '--meta', help='path to aci meta json file')

    # verify args
    args = parser.parse_args()
    if not args.klass and not args.list:
        parser.error("--class or --list required")
    elif args.klass and args.list:
        parser.error("only one of --class or --list required")

    # get list of classes to generate modules for
    if args.klass:
        classes = [args.klass]
    else:
        with open(args.list, 'r') as l:
            classes = list(map(lambda x: x.strip(), l.readlines()))

    if args.meta:
        with open(args.meta, 'r') as m:
            meta = m.read()
    else:
        meta = None

    classes = ansible_model(classes, meta)
    # with open(args.list, 'w') as n:
    #     n.write('\n'.join(classes))


if __name__ == '__main__':
    main()
