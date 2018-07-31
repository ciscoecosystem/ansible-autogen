#!/usr/bin/env python3

import argparse
import sys
import logging
import re
from jinja2 import Environment, FileSystemLoader
from object_model import MO, ModuleGenerationException

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
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)
# ------------------------------------------------------------------------------------

def render(template_name, context):
    env = Environment(loader=FileSystemLoader('.'))
    return env.get_template(template_name).render(context)

def main():
    #TODO: add arguments for other documentation sources
    parser = argparse.ArgumentParser(description='Create an Ansible Module for a specified ACI class')
    parser.add_argument('class_name', help='name of the class that the output module will manipulate')
    args = parser.parse_args()
    logger.info("Creating module for {0}".format(class_name))

    class_name = re.sub('[:-]', '', args.class_name)
    try:
        doc = MO(class_name=class_name)
        keys = doc.keys
        out = "generated_{0}_module.py".format(class_name)
        context = {'class': class_name,
                    'deletable': doc.deletable,
                    'keys': doc.keys,
                    'pkeys': doc.payload_keys,
                    'hierarchy': doc.hierarchy,
                    'doc': doc.doc,
                    'filename': out}
        with open(out, 'w') as f:
            mod = render('ansible_module.py.j2', context)
            f.write(mod)
    except ModuleGenerationException as e:
        logger.error(e)

    logger.info("Successfully created module for {0}".format(class_name))

if __name__ == '__main__':
    main()
