import os
import sys
from const import *
import file_handler
import hierarchy_handler
from logger import Logger
import aci_class_info_extracter

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_path)

from object_model import MIM


def gen_raml_module(aci_classes, meta):
    """
    main function that directs the flow of raml generation

    it get list of all aci classes,
    makes the copy of all the reference files,
    iterate through all aci classes and calls other function
    for each class to perform several tasks and in the
    end generate final raml file and deletes the copy of files

    Parameters
    ----------
    aci_classes : list
        list of aci classes whose raml needs to be generated
    meta : file
        json file which contains details of all aci classes
    """
    logger = Logger.get_logger(RAML_LOG_FILE)

    try:
        # creating a fresh directory by creating a copy of src_dir
        src_dir = '{}_temp'.format(RAML_DESTINATION_PATH)
        dest_dir = RAML_DESTINATION_PATH
        file_handler.copy_dir(src_dir, dest_dir)

        mim = MIM(meta)
        model = {klass: mim.get_class(klass, 'raml') for klass in aci_classes}

        # proper mapping of key value pair is important, key being the file whose copy will be made
        # and value being the copy of key file
        files_dict = {RAML_BASE_REFERENCE: RAML_BASE_TEMP, RAML_GET_ALL_OBJECTS_REFERENCE:
                      RAML_GET_ALL_OBJECTS_TEMP, RAML_CRUD_OBJECT_REFERENCE: RAML_CRUD_OBJECT_TEMP}
        file_handler.make_copy(files_dict)
    except Exception as err:
        logger.error('Program Execution failed and stopped. {}'.format(err))
        sys.exit()

    for klass, value in model.items():
        try:
            class_name = klass
            properties = value.properties.keys()
            label = aci_class_info_extracter.get_label(value, class_name)
            hierarchy = value.dnFormat
            is_creatable_deletable = value.isDeletable

            # if class has single dn, it is handled and rendered differently
            # than class which has multiple dn by hierarchy handler
            if len(hierarchy) == 1:
                hierarchy_handler.handle_single_hierarchy(
                    is_creatable_deletable, label, class_name, hierarchy)
            else:
                hierarchy_handler.handle_multiple_hierarchy(
                    is_creatable_deletable, label, class_name, hierarchy)

            # generating example file which contains the expected response of api request
            file_handler.generate_example_file(label, class_name)

            if is_creatable_deletable:
                file_handler.generate_property_file(
                    label, class_name, properties)
                # generating example file which contains the expected payload for create request
                file_handler.generate_create_object_example(
                    label, class_name, properties)
                # adding dataTypes in base raml file
                file_handler.add_dataTypes(label)
            else:
                logger.info(
                    'Create and Delete operation not available for class - {}.'.format(class_name))

        except Exception as err:
            logger.error(
                'Failed to create RAML for class - {}. {}'.format(class_name, err))

    try:
        # order of files in the list is important
        temp_files = [RAML_BASE_TEMP,
                      RAML_GET_ALL_OBJECTS_TEMP, RAML_CRUD_OBJECT_TEMP]
        # all the files in the list are appended to final raml file one by one
        file_handler.generate_raml(temp_files)
        file_handler.delete_files(temp_files)
    except Exception as err:
        logger.error(err)
