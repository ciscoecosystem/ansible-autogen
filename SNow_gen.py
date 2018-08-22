#!/usr/bin/env python3

import argparse
from jinja2 import Environment, FileSystemLoader
# from SNow_mim import MO
from object_model import MIM, MO
import logging

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


env = Environment(loader=FileSystemLoader('/Users/moimahmo/Desktop/SNow_scripting'))

def _get_contained_hierarchy(DEPTH, isAbstract, mim, contained, contained_props, labels):
    """
    draws from meta file
    returns list of lists
    each inner list defines a path from the queried
      class to the leaf or object at the specified depth
    """
    if DEPTH == 0: return [[]]
    if isAbstract: return [[]]
    if not contained: return [[]]
    #create list of lists
    contained_hierarchy = [[c] for c in contained]
    for c in contained: print(c)
    next_level = []
    for i in range(1, DEPTH):
        for path in contained_hierarchy:
            #print(i, path)
            if path[-1] in contained_props.keys():
                continue
            secondary_class = mim.get_class(path[-1])
            if secondary_class.isAbstract: continue
            contained_props[path[-1]] = list(secondary_class.properties.keys())
            if secondary_class.label:
                labels[path[-1]] = secondary_class.label.replace(' ', '_')
            else:
                labels[path[-1]] = path[-1]
            if secondary_class.contains != [[]]:
                if secondary_class.contains:
                    for c in secondary_class.contains:
                        if c in path: continue
                        next_level.append(path + [c])
                else:
                    next_level.append(path.copy())
        contained_hierarchy = next_level
    return contained_hierarchy

def _get_parent_labels(mim, _class, labels):
    for c in _class.dnFormat[0][1][:-1]:
        container = mim.get_class(c)
        labels[c] = container.label.replace(' ', '_')




def main():

    parser = argparse.ArgumentParser(description='Create a Service Now script for a specified ACI class')
    parser.add_argument('-c', '--class', help='name of the class to be queried', dest='klass')
    parser.add_argument('-m', '--meta', help='path to aci meta json file')
    parser.add_argument('-d', '--depth', help='depth of query within container tree')

    # verify args
    args = parser.parse_args()
    if not args.klass:
        parser.error("--class required")

    # get list of classes to generate modules for
    classes = [args.klass]

    if args.meta:
        with open(args.meta, 'r') as m:
            meta = m.read()
    else:
        meta = None

    class_name = args.klass
    if meta:
        mim = MIM(meta)

    if args.depth:
        DEPTH = int(args.depth)
    else: DEPTH = 2

    primary_class = mim.get_class(class_name)
    out = "generated_{0}_SNow_module.js".format(class_name)

    with open(out, 'w') as f:
        template = env.get_template("SNowTemplate.j2.txt")
        #class_name, e.g. fvTenant
        #parent_classes is a list of the containing classes in order of parent to child
            #for vzEntry, ["tenant", "filter"]
        #class_label is the label from the documentation, e.g. "filter_entry" for vzEntry
        #properties is the list of the names of the properties of a given class

        contained_props = {}
        labels = {}
        _get_parent_labels(mim, primary_class, labels)
        f.write(template.render({'name': class_name,
                'parent_classes': primary_class.dnFormat[0][1][1:-1],
                'label': primary_class.label.replace(' ', '_'),
                'properties': primary_class.properties.keys(),
                'hierarchy' : _get_contained_hierarchy(DEPTH, primary_class.isAbstract, mim,
                 primary_class.contains, contained_props, labels),
                'contained_props' : contained_props,
                'labels' : labels}))
if __name__ == '__main__':
    main()