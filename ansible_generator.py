#!/usr/bin/env python3

import argparse
import sys
import logging
import re
from jinja2 import Environment, FileSystemLoader
from object_model import MO, ModuleGenerationException

def gen_ansible_module(doc):
    generated_module = "generated_{class_name}_module.py".format(class_name=class_name)
    context = { 
                'class': class_name,
                'deletable': doc.deletable,
                'keys': doc.keys,
                'pkeys': doc.payload_keys,
                'hierarchy': doc.hierarchy,
                'doc': doc.doc,
                'filename': generated_module
            }
    with open(generated_module, 'w') as f:
        mod = render('templates/ansible_module.py.j2', context)
        f.write(mod)

