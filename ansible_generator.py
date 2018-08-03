#!/usr/bin/env python3

import argparse
import sys
import logging
import re
from utils import render
from object_model import MO, ModuleGenerationException

def gen_ansible_module(doc):
    class_name = doc.target_class
    generated_module = "generated_{class_name}_module.py".format(class_name=class_name)
    context = doc.ansible_get_context()
    extra_context = { 
                'deletable': doc.attributes["deletable"],
                'filename': generated_module
            }
    context.update(extra_context)

    
    with open(generated_module, 'w') as f:
        mod = render('templates/ansible_module.py.j2', context)
        f.write(mod)

