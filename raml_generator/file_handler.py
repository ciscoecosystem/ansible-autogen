import re
import os
import json
from jinja2 import Template
from collections import OrderedDict
from shutil import copyfile, copytree, rmtree

import data_manager
from const import *
from config import *
from exception_handler import handle_exception


@handle_exception
def make_copy(files_dict):
    """
    makes the copy of files

    it iterates key value pair from files_dict and
    makes copy of them, key being file to be
    copied and value being the destination file

    Parameters
    ----------
    files_dict : dict
        dictionary which contains key as file to be
        copied and value being the respective destination
        file
    """
    for key, value in files_dict.iteritems():
        copyfile(key, value)


@handle_exception
def copy_dir(src_dir, dest_dir):
    """
    create of copy of src_dir

    it creates a copy of src_dir on the path
    mentioned in dest_dir, if it already exists,
    overwrite it

    Parameters
    ----------
    src_dir : string
        path of source directory whose copy will be made
    dest_dir : string
        path of destination directory where copy will be made
    """
    if os.path.exists(dest_dir):
        rmtree(dest_dir)
    copytree(src_dir, dest_dir)


@handle_exception
def render_raml_template(label, label_with_parent, class_name, hierarchy, files_dict):
    """
    adding resources to raml file for aci class

    it adds resource of aci class to raml file, which include
    adding resource to get all objects, adding resource for
    crud operation on single object

    Parameters
    ----------
    label : string
        proper naming convention of aci class
    label_with_parent : string
        proper naming convention of aci class with parent
    class_name : string
        aci class whose resource needs to be added in raml file
    hierarchy : string
        hierarchy of aci class which forms url for aci class
        for crud operation on single object
    files_dict : dict
        contains key as template file and value as respective
        destination file
    """
    for key, value in files_dict.iteritems():
        with open(key) as file_:
            template = Template(file_.read())
        output_from_parsed_template = template.render(
            class_name=class_name, label=label, label_with_parent=label_with_parent, hierarchy=hierarchy)
        with open(value, 'a') as file_:
            file_.write('\n')
            file_.write(output_from_parsed_template)


@handle_exception
def generate_example_file(label, class_name, dest_path=RAML_DESTINATION_PATH):
    """
    generating example of response of api request

    it generates example file of how the response will look like
    for an api request on aci class. It logins into APIC,
    extract the token from the response, use that token to
    get response of the respective aci class (class_name),
    if there are multiple objects of respective aci class
    in response, extract single object and use it as a example

    Parameters
    ----------
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose example needs to be generated
    dest_path : string
        path of the destination file
    """
    response = data_manager.get_aci_data(class_name).json()
    if len(response['imdata']) >= 1:
        data = OrderedDict()
        data['totalCount'] = '1'
        data['imdata'] = [response['imdata'][0]]
        with open('{}/examples/expected_response/{}.json'.format(dest_path, label), 'w') as file_:
            json.dump(data, file_, indent=4)
    else:
        with open('{}/examples/expected_response/{}.json'.format(dest_path, label), 'w') as file_:
            json.dump(response, file_, indent=4)


@handle_exception
def generate_property_file(label, class_name, properties, template_file=RAML_PROPERTIES_TEMPLATE, dest_path=RAML_DESTINATION_PATH):
    """
    generating property file for aci class

    it generates property file for aci class which contains
    properties which are optional in payload of post request
    while creating object for an aci class

    Parameters
    ----------
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose type file needs to be generated
    properties : list
        optional properties required while creating object
        for an aci class 
    template_file : string
        template file which will be rendered to
        produce property file
    dest_path : string
        path of the destination file
    """
    with open(template_file) as file_:
        template = Template(file_.read())
    output_from_parsed_template = template.render(class_name=class_name)

    with open('{}/dataTypes/create_{}.raml'.format(dest_path, label), 'w') as file_:
        file_.write(output_from_parsed_template)

    with open('{}/dataTypes/create_{}.raml'.format(dest_path, label), 'a') as file_:
        for property_ in properties:
            file_.write('\n          {}?: string'.format(property_))


@handle_exception
def generate_create_object_example(label, class_name, properties, dest_path=RAML_DESTINATION_PATH):
    """
    generating example of creating a object of an aci class

    it generates example file of creating a object of an aci class
    for better understanding of how to create object of
    an aci class

    Parameters
    ----------
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose example needs to be generated
    properties : list
        properties optionally required to create object of aci class
    dest_path : string
        path of the destination file
    """
    data = {class_name: {'attributes': {}}}

    for property_ in properties:
        data[class_name]['attributes'][property_] = '{}_value'.format(
            property_)

    with open('{}/examples/expected_payload_for_creating_object/create_{}.json'.format(dest_path, label), 'w') as file_:
        json.dump(data, file_, indent=4)


@handle_exception
def add_dataTypes(label, dest_file=RAML_BASE_TEMP):
    """
    add 'dataTypes' to base reference raml file
    types - raml terminology

    it add dataTypes for each of the aci class to base
    reference raml file

    Parameters
    ----------
    label : string
        proper naming convention of aci class
    dest_file : string
        file in which types will be added
    """
    with open(dest_file, 'a') as file_:
        file_.write('\n  ')
        file_.write(
            'create_{0}: !include dataTypes/create_{0}.raml'.format(label))


@handle_exception
def generate_raml(src_files, dest_path=RAML_DESTINATION_PATH):
    """
    creates a final raml file

    it creates a final raml file by combining all
    refrence raml file

    Parameters
    ----------
    src_files : list
        list of files which will be appended
        to final destination file
    dest_path : string
        path of the destination file
    """
    for input_file in src_files:
        with open(input_file) as file_:
            with open('{}/cisco_aci.raml'.format(dest_path), 'a') as output_file:
                for line in file_:
                    output_file.write(line)


@handle_exception
def delete_files(files_list):
    """
    delete files

    deletes the list of files which is passed to this
    function

    Parameters
    ----------
    files_list : list
        list of files which need to be deleted
    """
    for file_ in files_list:
        os.remove(file_)
