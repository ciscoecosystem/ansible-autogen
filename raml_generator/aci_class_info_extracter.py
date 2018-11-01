import re
from exception_handler import handle_exception


@handle_exception
def get_label(value, class_name):
    """
    extract label from 'value'

    it extract label from 'value' for better understanding of user
    (label - aci class being referred) and joins class name with label

    Parameters
    ----------
    value : object
        details of aci class
    class_name : string
        aci class whose label need to be extracted from 'data'
    Returns
    -------
    label : string
        label of aci class
    """
    label = ''
    label = value.label

    if not label:
        raise Exception(
            'No label found in json file for aci class - {}'.format(class_name))

    label = '{}-{}'.format(class_name, label)
    for char in [' ', '/', '_']:
        label = label.replace(char, '-')
    label = re.sub('--+', '-', label)
    label = label.lower()

    return label


@handle_exception
def get_hierarchy_url(hierarchy_url, label, class_name):
    """
    gets url from hierarchy

    it gets url from hierarchy for REST request
    to create a object of aci class

    Parameters
    ----------
    hierarchy : string
        hierarchy of aci class
    label : string
        proper naming convention of aci class
    class_name : string
        aci class whose url needs to be generated
    Returns
    -------
    hierarchy_url : string
       url for REST request
    """
    current_class = hierarchy_url.rsplit('/', 1)[-1]
    brackety_string = re.findall('\{(.*?)\}', current_class)

    # modifying last uri parameter of url by attaching class name and label to it
    # for better understanding
    for curr_bracket in brackety_string:
        modified_bracket = '{{{}-{}}}'.format(label, curr_bracket)
        hierarchy_url = hierarchy_url.replace(
            '{'+curr_bracket+'}', modified_bracket)

    # converting all uri parameters to lower case
    for curr_bracket in re.findall('\{(.*?)\}', hierarchy_url):
        hierarchy_url = hierarchy_url.replace(
            '{'+curr_bracket+'}', '{'+curr_bracket.lower()+'}')

    # encoding URL
    hierarchy_url = hierarchy_url.replace('[', '%5B').replace(']', '%5D')
    hierarchy_url = hierarchy_url.replace('_', '-')
    hierarchy_url = re.sub('--+', '-', hierarchy_url)

    return hierarchy_url


@handle_exception
def get_immediate_parent(hierarchy):
    """
    get the parent class of current aci class

    it gets the parent class of current aci class dn
    for distinct labeling of classes which have
    multiple hierarchies

    Parameters
    ----------
    hierarchy : list
        hierarchy of aci class
    Returns
    -------
    immediate_parent : string
        returns the parent of current aci class dn
    """
    immediate_parent = hierarchy[-2]
    for char in [' ', '_']:
        immediate_parent = immediate_parent.replace(char, '-')

    immediate_parent = re.sub('--+', '-', immediate_parent)
    immediate_parent = immediate_parent.lower()

    return immediate_parent
