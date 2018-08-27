
#!/usr/bin/env python3

import argparse
import sys
import logging
import re
import json
from utils import render
from object_model import MIM, ModuleGenerationException
from ansible_generator import gen_ansible_module
from terraform_generator import *
# ====================================================================================
# Logging
# ------------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("module.log")
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
# # Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)
# # ------------------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description='Utility to create Module for a specified ACI class')
    parser.add_argument("-m","--meta", help="Location of the meta json file", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ansible', action='store_true', help='generate code for ansible module')
    group.add_argument('--terraform', action='store_true', help='generate model and service code for terraform provider')
    class_input_group = parser.add_mutually_exclusive_group(required=True)
    class_input_group.add_argument('-c', '--class', help='name of the class that the output module will manipulate', dest='klass')
    class_input_group.add_argument('-l', '--list', help='path of text file containing class names')

    args = parser.parse_args()

    meta = None
    classes = None

    # get list of classes to generate modules for
    if args.klass:
        classes = [args.klass]
    else:
        with open(args.list, 'r') as l:
            classes = list(map(lambda x: x.strip(), l.readlines()))

    if args.meta:
        with open(args.meta, 'r') as m:
            meta = m.read()

    try:
        # doc = MO(class_name=class_name)
        # print(json.dumps(doc.terraform_get_context()))
        if args.ansible:
            classes = gen_ansible_module(classes, meta)

        elif args.terraform:
            pass 
            gen_go_service(classes, meta)
            gen_go_module(classes, meta)
            gen_terraform_resource(classes, meta)
    except ModuleGenerationException as e:
        logger.error(e)

    logger.info("Successfully created module for {0}".format(classes))

if __name__ == '__main__':
    main()
