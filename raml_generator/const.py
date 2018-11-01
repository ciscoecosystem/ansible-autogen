from os.path import join, dirname

"""
some constant variables path, url, python command, etc. which will be used by raml_generator 
"""

# path of the folder which contains all the files related to RAML automation
BASE_PATH = dirname(__file__)

# path of the folder which contains all the templates required for automation
TEMPLATE_PATH = join(BASE_PATH, 'templates')

# path of the folder which contains all the raml references required for automation
REFERENCE_PATH = join(BASE_PATH, 'references')

# path of the template file which has the raml template to get all objects of a aci class
RAML_GET_ALL_OBJECTS_TEMPLATE = join(TEMPLATE_PATH, 'get_all_objects.raml')

# path of the template file which has the raml template to create, update, get and delete an object of a aci class
RAML_CRUD_OBJECT_TEMPLATE = join(TEMPLATE_PATH, 'crud_object.raml')

# path of the template file which has the raml template to get object of a aci class.
# two different files for crud and get object because some classes does not support creation
# and deletion of object but support reading the object
RAML_GET_OBJECT_TEMPLATE = join(TEMPLATE_PATH, 'get_object.raml')

# path of the template file which has the raml template to store the properties of a aci class
RAML_PROPERTIES_TEMPLATE = join(TEMPLATE_PATH, 'properties.raml')

# path of raml file which has the base of main raml file i.e beginning of main raml file which is constant.
# dataTypes of all aci class will be appended in this raml file
RAML_BASE_REFERENCE = join(REFERENCE_PATH, 'base_reference.raml')

# path of raml file which has aci login resource as it will remain constant and beginning of resource
# used to get all objects of a aci class. Resources of all aci class to get all objects will be appended in this file
RAML_GET_ALL_OBJECTS_REFERENCE = join(
    REFERENCE_PATH, 'get_all_objects_reference.raml')

# path of raml file which has beginning of resource used to get, create, update and delete an object of a aci class.
# Resources to get, create, update and delete an object of all aci class will be appended in this file
RAML_CRUD_OBJECT_REFERENCE = join(REFERENCE_PATH, 'crud_object_reference.raml')

# path of temp file which will be created and deleted in the execution process, it will be copy of base_reference.raml
RAML_BASE_TEMP = join(REFERENCE_PATH, 'base_temp.raml')

# path of temp file which will be created and deleted in the execution process, it will be copy of get_all_objects_reference.raml
RAML_GET_ALL_OBJECTS_TEMP = join(REFERENCE_PATH, 'get_all_objects_temp.raml')

# path of temp file which will be created and deleted in the execution process, it will be copy of crud_object_reference.raml
RAML_CRUD_OBJECT_TEMP = join(REFERENCE_PATH, 'crud_object_temp.raml')

# path of the folder where all the generated raml will be stored
RAML_DESTINATION_PATH = join(BASE_PATH, 'gen', 'cisco_aci')

# path of log file where all the logs related to code will be added
RAML_LOG_FILE = join(BASE_PATH, 'aci_raml.log')
