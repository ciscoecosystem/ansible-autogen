from const import *
import file_handler
import aci_class_info_extracter
from exception_handler import handle_exception


@handle_exception
def handle_single_hierarchy(is_creatable_deletable, label, class_name, hierarchy):
    """
    handles aci classes which have single hierarchy

    get hierarchy url of aci class hierarchy and
    calls the render raml template to form a raml
    for this aci class. Whether to form a raml of
    creating/deleting a object depends on
    is_creatable_deletable

    Parameters
    ----------
    is_creatable_deletable : bool
        True if object of class_name could be created or deleted
        else False
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose hierarchy needs to be added in raml file
    hierarchy : list
        hierarchy of aci class which forms url for aci class
        for crud operation on single object
    """
    hierarchy_url = aci_class_info_extracter.get_hierarchy_url(
        hierarchy[0][0], label, class_name)

    # proper mapping of key value pair is important
    # key being the template file which will be rendered
    # and value being the destinaton file where rendered template will be appended

    # for classes whose object can be created or deleted, RAML_CRUD_OBJECT_TEMPLATE is used
    # else RAML_GET_OBJECT_TEMPLATE is used
    if is_creatable_deletable:
        file_handler.render_raml_template(label, label, class_name, hierarchy_url, {
            RAML_GET_ALL_OBJECTS_TEMPLATE: RAML_GET_ALL_OBJECTS_TEMP, RAML_CRUD_OBJECT_TEMPLATE: RAML_CRUD_OBJECT_TEMP})
    else:
        file_handler.render_raml_template(label, label, class_name, hierarchy_url, {
            RAML_GET_ALL_OBJECTS_TEMPLATE: RAML_GET_ALL_OBJECTS_TEMP, RAML_GET_OBJECT_TEMPLATE: RAML_CRUD_OBJECT_TEMP})


@handle_exception
def handle_multiple_hierarchy(is_creatable_deletable, label, class_name, hierarchies):
    """
    handles aci classes which have multiple hierarchy

    traverse the list of hierarchies and get hierarchy
    url of aci class hierarchy and calls the render
    raml template to form a raml for this aci class.
    Whether to form a raml of creating/deleting a
    object depends on is_creatable_deletable

    Parameters
    ----------
    is_creatable_deletable : bool
        True if object of class_name could be created or deleted
        else False
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose hierarchy needs to be added in raml file
    hierarchies : list
        list of hierarchy of aci class which forms url for
        aci class for crud operation on single object
    """
    # rendering GET_ALL_OBJECTS_TEMPLATE before for loop
    # as rendering for this template should be once for each class
    file_handler.render_raml_template(label, label, class_name, '', {
        RAML_GET_ALL_OBJECTS_TEMPLATE: RAML_GET_ALL_OBJECTS_TEMP})
    # set which will store the hierarchies of the class for which raml is already created
    # for example two dn are similiar in documentation of class - fvnsEncapBlk
    raml_done_for_hierarchy = set()

    for hierarchy in hierarchies:
        hierarchy_url = aci_class_info_extracter.get_hierarchy_url(
            hierarchy[0], label, class_name)
        immediate_parent = aci_class_info_extracter.get_immediate_parent(
            hierarchy[1])
        # appending label with immediate parent for better understanding and
        # if two connectors have same label, anypoint studio appends number
        # ahead of label, so instead of number, here immediate_parent is appended
        label_with_parent = '{}-through-{}'.format(label, immediate_parent)

        # if raml for hierarchy is already created, ignore it
        if hierarchy_url in raml_done_for_hierarchy:
            continue

        raml_done_for_hierarchy.add(hierarchy_url)

        # proper mapping of key value pair is important
        # key being the template file which will be rendered
        # and value being the destinaton file where rendered template will be appended

        # for classes whose object can be created or deleted, RAML_CRUD_OBJECT_TEMPLATE is used
        # else RAML_GET_OBJECT_TEMPLATE is used
        if is_creatable_deletable:
            file_handler.render_raml_template(label, label_with_parent, class_name, hierarchy_url, {
                RAML_CRUD_OBJECT_TEMPLATE: RAML_CRUD_OBJECT_TEMP})
        else:
            file_handler.render_raml_template(label, label_with_parent, class_name, hierarchy_url, {
                RAML_GET_OBJECT_TEMPLATE: RAML_CRUD_OBJECT_TEMP})
