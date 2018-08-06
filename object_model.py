from keyword import iskeyword
import re
import requests
import io
import sys
import json

# Dictionary of Regex Patterns to pull properties from documentation html files:
rp = {  'cleanr': re.compile("<.*?>"),
        'del':re.compile("Creatable/Deletable:\s*?([a-z]+)"),
        'dn_format': re.compile("DN FORMAT:(.*)", re.DOTALL),
        'dn_component': re.compile("(?:\w+-\{.+?\})|(?:\w+)|(?:\{.+?\})"),
        'dn_prefix_prop': re.compile("(\w+)?-?(\{\[?(\w+)\]?\})?"),
        'dn_line': re.compile("\[[0-9]*\](.*)"),
        'doc_descr': re.compile("</h4>(.*?)<br/>\s+<br/>.*?NAMING RULE", re.DOTALL),
        'href': re.compile("href=\"MO-(.*?).html"),
        'label': re.compile("Class Label:(.*)"),
        'name_colon': re.compile("mo\[(.+?)\]"),
        'name_split': re.compile("([a-zA-Z]+):([a-zA-Z]+)"),
        'prop_name': re.compile("<h3>([a-zA-Z]+)</h3>"),
        'prop_options': re.compile("<font size=\"-1\"> (.*?) </font>"),
        'rn_format': re.compile("RN FORMAT:(.*)"),
        'rn_prefix': re.compile("PREFIX=(.*?)[-\n]"),
        't_a': re.compile("<a.*?>(.*?)</a>", re.DOTALL),
        't_pre': re.compile("<pre>(.*?)</pre>", re.DOTALL),
        }

class MO:
    """
    Gets all necessary class properties of an ACI class to create a corresponding
    Ansible module.  Stores information in instance variables.
    -------------
    self.properties: dict
        dictionary with keys are class property names
        values are dictionaries with keys: ['options', 'label']
            self.property['options']: list of strings, valid options for given class property
            self.property['label']: string, description of property

    self.attributes: dict
        keys are class attribute names
            ex: ['deletable', 'description', 'label', 'name']
        values are attribute values
            for class fvAEPg
            ex: [True, 'A set of requirements for the application-level EPG instance. The policy regulates connectivity and visibility among the end points within the scope of the policy.', 'Application EPG', 'fv:AEPg']

    self.hierarchy: list
        values are lists of strings: names of classes in the container hierarchy,
        from highest level to lowest, always ending at the target class

        example for fvAEPg: [['polUni', 'fvTenant', 'fvAp', 'fvAEPg']]

    self.naming: dict
        keys are all class names that appear in self.hierarchy

        values are tuples: (properties, label)
            properties: list of dicts representing prefix/property pairs for the class rn
                containing dicts with keys [prefix, property, delimiters, comments]

                RN for fvnsVlanInstP: "vlanns-{[name]}-{allocMode}"
                properties = [{'prefix': 'vlanns',
                                'property': 'name',
                                'delimiters': True,
                                'comments': 'The VLAN range namespace policy name.'},
                              {'prefix': '',
                               'property': 'allocMode',
                               'delimiters': False,
                               'comments': 'The allocation mode of the VLAN pool.'}]
                label: string
                    class label
                    example for fvnsVlanInstP:  'VLAN Pool'
    """

    def __init__(self, class_name):
        """Gathers all relevant properties of a ACI class as instance variables"""
        self.target_class = class_name
        self.properties = {}
        self.attributes = {}
        self.hierarchy = []
        self.naming = {}

        self._initialize_html()


    def ansible_get_context(self):
        """return information needed to generate an Ansible module for target class"""
        all_parameters = self.properties # TODO deep copy this
        for key, value in all_parameters.items(): # set python variable name for Ansible module, avoid keywords
            value['payload'] = key
            if iskeyword(key):
                value['var'] = "_" + key
            else:
                value['var'] = key

        doc = self.attributes

        #create payload keys, properties in aci json payload only
        payload_parameters = {} #target class properties only
        for key, value in all_parameters.items():
            if "payload" in value:
                payload_parameters[key] = value

        #create hierarchy
        hierarchy = self._ansible_get_hierarchy(all_parameters)

        return {'class': self.target_class,
                'keys': all_parameters,
                'pkeys': payload_parameters,
                'hierarchy': hierarchy,
                'doc': doc}

    def terraform_get_context(self):
        """return information needed to generate an Ansible module for target class"""
        all_parameters = self.properties # TODO deep copy this
        for key, value in all_parameters.items(): # set python variable name for Ansible module, avoid keywords
            value['payload'] = key
            if iskeyword(key):
                value['var'] = "_" + key
            else:
                value['var'] = key

        doc = self.attributes

        doc["slug_label"] = doc["label"].replace(" ","")

        #create payload keys, properties in aci json payload only
        payload_parameters = {} #target class properties only
        for key, value in all_parameters.items():
            if "payload" in value:
                payload_parameters[key] = value

        #create hierarchy
        hierarchy = self._ansible_get_hierarchy(all_parameters)

        return {'class': self.target_class,
                'keys': all_parameters,
                'pkeys': payload_parameters,
                'hierarchy': hierarchy,
                'doc': doc}


    def SN_get_context(self):
        """return information needed to generate a Service Now script"""
        return {'name': self.target_class,
                'parent_classes': self.hierarchy[0],
                'label': self.attributes['label'].lower().replace(" ", "_"),
                'properties': self.properties.keys(),
                }


    def _ansible_get_hierarchy(self, all_parameters):
        """return hierarchy list for Ansible context"""
        # TODO figure out choosing DN/container heirarchy
        if len(self.hierarchy) == 0:
            raise InvalidDNException("Documentation does not contain DN info")

        chain = self.hierarchy[0]

        hierarchy = []

        unnamed_parent = "" # for getting "rn" argument for aci.py contruct_url()
        for class_name in chain:
            components, label = self.naming[class_name]
            label = label.lower().replace(" ", "_")
            rn_str = ""
            class_naming = {'name': class_name}
            naming_args = []
            naming_props= []
            for component in components:
                # add parameters to dictionary
                if component['property'] != '':
                    details = {'comments': component['comments'], 'naming': True}
                    if class_name != self.target_class:
                        prop = label if component['property'] == "name" else "{0}_{1}".format(label, component['property'])
                        details['var'] = prop
                    else:
                        prop = component['property']
                        if iskeyword(component['property']):
                            details['var'] = "_{0}".format(component['property'])
                        else:
                            details['var'] = component['property']
                        if component['property'] == 'name':
                            details['aliases'] = [label]
                        details['payload'] = component['property']
                    all_parameters[prop] = details
                    naming_args.append(details['var'])
                    naming_props.append(component['property'])

                # construct component string
                print(component.keys())
                if component['delimiters']:
                    comp_str = "{0}-[{{}}]".format(component['prefix'], component['property'])
                elif component['property'] == '':
                    comp_str = component['prefix']
                elif component['prefix'] == '':
                    comp_str = "{}"
                else:
                    comp_str = "{0}-{{}}".format(component['prefix'])
                rn_str = rn_str + comp_str if rn_str == '' else rn_str + "-" + comp_str

            # construct relative name format string


            # construct filter string
            if len(naming_args) != 0:
                arg_str = "("
                i = 0
                while i < len(naming_args) - 1:
                    arg_str += naming_args[i] + ", "
                    i += 1
                arg_str += naming_args[-1] + ")"
            else:
                arg_str = "()"

            if len(naming_args) == 0:
                 filter_str = ""
            elif len(naming_args) == 1:
                 filter_str = "\'eq({0}.{1}, \"{{}}\")\'.format({2})".format(class_name, naming_props[0], naming_args[0])
            else:
                filter_str = "\'and("
                i = 0
                while i < len(naming_args) - 1:
                    filter_str += "eq({0}.{1}, \"{{}}\"),".format(class_name, naming_props[i])
                    i += 1
                filter_str += "eq({0}.{1}, \"{{}}\"))\'.format{2}".format(class_name, naming_props[i], arg_str)

            # prepend parent classes if necessary
            if '{' not in rn_str and class_name != self.target_class: # unspecified class
                unnamed_parent += rn_str + "/"
            elif '{' not in rn_str: # unnamned target class
                rn_str = unnamed_parent + rn_str
                class_naming['args'] = [None]
                class_naming['rn'] = "\'{0}\'".format(rn_str)
                class_naming['filter'] = "\'\'"
                hierarchy.append(class_naming)
            else:
                rn_str = unnamed_parent + rn_str
                unnamed_parent = ""
                class_naming['args'] = naming_args
                class_naming['rn'] = "\'{0}.format{1}".format(rn_str, arg_str)
                class_naming['filter'] = filter_str
                hierarchy.append(class_naming)

        return hierarchy


    def _initialize_html(self):
        """initialize instance variables using online HTML documentation"""
        r = requests.get("https://pubhub.devnetcloud.com/" + \
            "media/apic-mim-ref-311/docs/MO-{0}.html".format(self.target_class))
        if r.status_code != 200:
            raise InvalidURLException("class documentation request failed")
        html = r.text

        # initialize self.properties
        all_properties = rp['prop_name'].findall(html)
        num_total = len(all_properties)
        property_doc_tags = rp['t_pre'].findall(html)[4:] # html doc corresponding to each property; first 4 always other docs, no properties

        for i in range(num_total):
            cur = all_properties[i]
            if "admin" in property_doc_tags[i]:
                details = {}
                options = MO._get_property_details(cur, html)
                details['options'] = options
                details['label'] = self._get_property_comments(cur, html)
                self.properties[cur] = details


        # initialize self.attributes
        self.attributes['label'] = rp['label'].search(html).group(1).strip()
        self.attributes['deletable'] = True if rp['del'].search(html).group(1) == 'yes' else False
        self.attributes['description'] = rp['doc_descr'].search(html).group(1).strip()
        self.attributes['name'] = rp['name_colon'].search(html).group(1)

        # initialize self.hierarchy
        name_text = rp['t_pre'].search(html).group(1) # string containing HTML doc snippet of the RN and DN naming conventions

        class_names = set() # keys for self.naming
        dn_text = rp['dn_format'].search(name_text).group(1) # get all classes relevant to the distinguished name
        dn_options = rp['dn_line'].findall(dn_text) #list of html strings, dn choices
        for option in dn_options:
            classes = rp['href'].findall(option)
            self.hierarchy.append(classes)
            class_names.update(classes)

        # populate self.naming
        for class_name in class_names:
            properties, label = MO._get_class_naming(class_name)
            self.naming[class_name]= (properties, label)

    @staticmethod
    def _clean_html(raw_html):
        """removes html brackets"""
        return re.sub(rp['cleanr'], "", raw_html)

    @staticmethod
    def _get_class_naming(class_name):
        """
        Parameters
        ----------
        class_name : str
            name of ACI class

        Returns
        -------
        name_component_properties: list
            list of dicts, value is self.naming[class_name][0]
            see instance variable documentation

        label: str
            class label
        """
        r = requests.get("https://pubhub.devnetcloud.com/" + \
            "media/apic-mim-ref-311/docs/MO-{0}.html".format(class_name))

        label = rp['label'].search(r.text).group(1).strip()

        rn_text = rp['rn_format'].search(r.text).group(1).strip()
        rn_text = MO._clean_html(rn_text)

        name_comp = rp['dn_component'].findall(rn_text)
        name_component_properties = []
        for comp in name_comp:
            match = rp['dn_prefix_prop'].search(comp)
            prefix = '' if not match.group(1) else match.group(1)
            property = '' if not match.group(3) else match.group(3)
            delimiters = False if not match.group(2) else '[' in match.group(2)

            if property != '': # get comments on property if it exists
                comments = MO._get_property_details(property, r.text)
            else:
                comments = None

            name_component_properties.append({
                'prefix': prefix,
                'property': property,
                'delimiters': delimiters,
                'comments': comments})

        return name_component_properties, label

    @staticmethod
    def _get_property_comments(property_name, doc_text):
        """
        Parameters
        ----------
        property_name : str
            name of object property
        doc_text : str
            html documentation for the relevant ACI class

        Returns
        -------
        str
            comments of the property from the documentation
        """
        pd = "<a name=\"{0}\".*?<br/>".format(property_name)
        re_pd = re.compile(pd, re.DOTALL)
        text = re_pd.search(doc_text).group()

        re_des = re.compile("<dd>(.*?)</dd>", re.DOTALL)
        descr = re_des.search(text).group(1).strip()
        descr = re.sub("\n", " ", descr)  # removing excess whitespace
        return re.sub("\s+", " ", descr)

    @staticmethod
    def _get_property_details(property_name, html):
        """
        Parameters
        ----------
        property_name : str
            name of object property
        html: str
            html documentation for the relevant ACI class

        Returns
        -------
        list
            list of strings, valid values for a property
            empty list if property is not constrained
        """
        pd = "<a name=\"{0}\".*?<br/>".format(property_name)
        re_pd = re.compile(pd, re.DOTALL)
        text = re_pd.search(html).group()

        val = rp['prop_options'].findall(text)
        return val

    @staticmethod
    def _name_split(fullname):
        """
        Parameters
        ----------
        property_name : str
            name of ACI class formatted as: '<package>:<name>'
            ex: 'fv:Tenant'

        Returns
        -------
        package: str
            package name
            ex: 'fv'
        name: str
            class name
            ex: 'Tenant'
        """
        match = rp['name_split'].search(fullname)
        package = match.group(1)
        name = match.group(2)
        return package, name

class ModuleGenerationException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidDNException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)

class InvalidURLException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)
