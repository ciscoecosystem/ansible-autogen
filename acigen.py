
#!/usr/bin/env python3

import argparse
import sys
import logging
import re
import json
from utils import render
from object_model import MO, ModuleGenerationException
from ansible_generator import gen_ansible_module

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
# Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)
# ------------------------------------------------------------------------------------


def main():
    #TODO: add arguments for other documentation sources
    parser = argparse.ArgumentParser(description='Utility to create Module for a specified ACI class')
    parser.add_argument('class_name', help='name of the class that the output module will manipulate')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ansible', action='store_true', help='generate code for ansible module')
    group.add_argument('--terraform', action='store_true', help='generate model and service code for terraform provider')

    args = parser.parse_args()

    class_name = re.sub('[:-]', '', args.class_name)
    logger.info("Creating module for {0}".format(class_name))
    try:
        doc = MO(class_name=class_name)
        print(doc)
        if args.ansible:
            gen_ansible_module(doc)
        elif args.terraform:
            pass
            
            
    except ModuleGenerationException as e:
        logger.error(e)

    logger.info("Successfully created module for {0}".format(class_name))

if __name__ == '__main__':
    main()
