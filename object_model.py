from keyword import iskeyword
import re
import requests
import io
import sys

#Dictionary of Regex Patterns to pull properties from documentation html files:
rp = {  'cleanr': re.compile("<.*?>"),
        'del':re.compile("Creatable/Deletable:\s*?([a-z]+)"),
        'dn_format': re.compile("DN FORMAT:(.*)", re.DOTALL),
        'dn_line': re.compile("\[[0-9]*\](.*)"),
        'doc_descr': re.compile("</h4>(.*?)<br/>\s+<br/>.*?NAMING RULE", re.DOTALL),
        'href': re.compile("href=\"MO-(.*?).html"),
        'label': re.compile("Class Label:(.*)"),
        'name_colon': re.compile("mo\[(.+?)\]"),
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
    self.doc: dict
        dictionary with the target class label, name and description

    self.hierarchy: list
        list of dictionaries, corresponding to all classes that must be specified
        in the target class's distinguished name, in order of parent to child
        Dictionary contains class name, naming parameters, and RN/filter format strings.

    self.keys: dict
        keys of the dictionary are parameters for the Ansible module
        values are dictionaries that contain parameter info

    self.naming: list
        list of outward facing ansible parameters that are required to name a MO

    self.payload_keys: dict
        dictionary with keys as a subset of self.keys that are required for a
        POST payload
    """

    def __init__(self, class_name=None):
        """Gathers all relevant properties of a ACI class as instance variables"""
        r = requests.get("https://pubhub.devnetcloud.com/" + \
            "media/apic-mim-ref-311/docs/MO-{0}.html".format(class_name))
        if r.status_code != 200:
            raise InvalidURLException("class documentation request failed")
        self.text = r.text
        self.target_class = class_name

        #determine if class can be created/deleted
        self.deletable = True if rp['del'].search(self.text).group(1) == 'yes' else False

        self._set_ansible_keys()
        self._set_class_heirarchy()
        self._set_documentation()

    def _clean_html(self, raw_html):
        """removes html brackets"""
        return re.sub(rp['cleanr'], "", raw_html)

    def _construct_rn_string(self, format, args, props, class_name, parent_string):
        """
        Parameters
        ----------
        format: str
            name of class with prefix
        args: list
            list of strings, variable names that will be used in the Ansible module
        props: list
            list of strings, aci MIM property names
        class_name: str
            class name with prefix
        parent_string: str
            string with rn's of unnamed parent classes

        Returns
        -------
        python code snippets that will go in module template.

        rn: str
            relative name format with str.format method on naming variables
        filter_str: list
            filter string
        """

        #contruct rn format string
        if len(args) != 0:
            arg_str = "("
            i = 0
            while i < len(args) - 1:
                arg_str += args[i] + ", "
                i += 1
            arg_str += args[-1] + ")"
        else:
            arg_str = "()"
        rn =  "\'{0}{1}\'.format{2}".format(parent_string, format, arg_str)

        #contruct filter string
        if len(args) == 0:
            filter_str = ""
        elif len(args) == 1:
            filter_str = "\'eq({0}.{1}, \"{{}}\")\'.format({2})".format(class_name, props[0], args[0])
        else:
            filter_str = "\'and("
            i = 0
            while i < len(args) - 1:
                filter_str += "eq({0}.{1}, \"{{}}\"),".format(class_name, props[i])
                i += 1
            filter_str += "eq({0}.{1}, \"{{}}\"))\'.format{2}".format(class_name, props[i], arg_str)

        return rn, filter_str

    def _get_class_name_props(self, class_name):
        """
        Parameters
        ----------
        class_name : str
            name of class with prefix

        Returns
        -------
        rn_format_string: str
            string with prefixes and brackets for naming arguments, ex: 'tn-{}', 'from-[{}]-to-[{}]'
        name_args: list
            list of strings, outward facing ansible parameter names for the aci class
        name_props: list
            list of strings, aci MIM parameter names for the aci class
        descriptions: list
            list of strings, aci documentation comments for each naming property
        """
        r = requests.get("https://pubhub.devnetcloud.com/" + \
            "media/apic-mim-ref-311/docs/MO-{0}.html".format(class_name))
        label = rp['label'].search(r.text).group(1).strip().lower().replace(" ", "_")
        prefix = rp['rn_prefix'].search(r.text).group(1).strip()

        if class_name == self.target_class:
            self.label = label

        #get relative name arguments and format
        rn_text = rp['rn_format'].search(r.text).group(1).strip()
        rn_text = self._clean_html(rn_text)
        delimiters = "(\{\[|\{).*?(\]\}|\})" #pattern to remove paramter names
        group_args = re.compile("(?:\{\[|\{)(.*?)(?:\]\}|\})") #pattern to extract paramters from search().group()
        replace = "\g<1>\g<2>" # replacement
        flip_brackets = "(\{\[).*?(\]\})" #pattern to sub {[]} to [{}]

        name_props = group_args.findall(rn_text)
        rn_format_string = re.sub(delimiters, replace, rn_text)
        rn_format_string = re.sub(flip_brackets, "[{}]", rn_format_string)

        #if rn argument is 'name', replace with the class label
        #otherwise, prepend class label to naming argument
        if class_name != self.target_class:
            name_args = [label if arg == "name" else label+"_"+arg for arg in name_props]
        else:
            name_args = name_props[:]

        #get property descriptions
        descriptions = [self._get_property_comments(prop, doc_text=r.text)
                        for prop in name_props]

        return rn_format_string, name_args, name_props, descriptions

    def _get_property_comments(self, property_name, doc_text=None):
        """
        Parameters
        ----------
        property_name : str
            name of object property
        doc_text : str
            html documentation

        Returns
        -------
        str
            comments of the property from the documentation
        """
        if not doc_text:
            doc_text = self.text
        pd = "<a name=\"{0}\".*?<br/>".format(property_name)
        re_pd = re.compile(pd, re.DOTALL)
        text = re_pd.search(doc_text).group()

        re_des = re.compile("<dd>(.*?)</dd>", re.DOTALL)
        descr = re_des.search(text).group(1).strip()
        descr = re.sub("\n", " ", descr) #removing excess whitespace
        return re.sub("\s+", " ", descr)

    def _get_property_details(self, property_name):
        """
        Parameters
        ----------
        property_name : str
            name of object property

        Returns
        -------
        list
            list of strings, valid values for a property
            empty list if property is not constrained
        """
        pd = "<a name=\"{0}\".*?<br/>".format(property_name)
        re_pd = re.compile(pd, re.DOTALL)
        text = re_pd.search(self.text).group()

        val = rp['prop_options'].findall(text)
        return val

    def _get_unnamed_props(self, class_name):
        return


    def _set_ansible_keys(self):
        """sets self.keys variable on target class properties"""
        print("Getting {0} class properties".format(self.target_class))
        #list of strings, names of all object properties
        all_properties = rp['prop_name'].findall(self.text)
        num_total = len(all_properties)
        #list of html documentation corresponding to each property
        property_doc_tags = rp['t_pre'].findall(self.text)[4:]

        self.keys = {}
        for i in range(num_total):
            cur = all_properties[i]
            if "admin" in property_doc_tags[i]:
                details = {}
                options = self._get_property_details(cur)
                details['options'] = options
                details['payload'] = cur
                details['comments'] = self._get_property_comments(cur)
                if iskeyword(cur):
                    details['var'] = "_" + cur
                else:
                    details['var'] = cur
                self.keys[cur] = details

    def _set_class_heirarchy(self):
        """set self.hierarchy variable to determine parents classes"""
        print("Getting all naming properties")

        #string containing HTML doc snippet of the RN and DN naming conventions
        name_text = rp['t_pre'].search(self.text).group(1)

        #get all classes relevant to the distinguished name
        dn_text = rp['dn_format'].search(name_text).group(1)
        dn_options = rp['dn_line'].findall(dn_text) #list of strings,

        #take user input for distinguished name format
        if len(dn_options) == 0:
            raise InvalidDNException("Online documentation for {0} does not contain DN info.".format(self.target_class))
        elif len(dn_options) == 1:
            choice = 0
        else:
            for i in range(len(dn_options)):
                print(str(i+1) + ": " +  self._clean_html(dn_options[i]))
            print(self.target_class)
            choice = int(input("Enter number corresponding to desired DN format\n"))-1

        #extract classes that must be specified in the distinguished name
        dn_html = dn_options[choice]
        dn_parameters = rp['href'].findall(dn_html)
        name_components = rp['t_a'].findall(dn_html)

        #prepend unnamed parents classes for 'aci_rn' in construct_url() in 'aci.py'
        specified_class_name = [] #class name for lookup later
        unnamed_parents = [] #unnamed parent classes prior to named class, aci util module needs it to construct url
        parents_temp = ""
        unnamed_target = False
        for i in range(len(name_components)):
            if "{" in name_components[i]:
                specified_class_name.append(dn_parameters[i])
                unnamed_parents.append(parents_temp)
                parents_temp = ""
            elif i == len(name_components) - 1: #target class is unnamed
                unnamed_target = True
            elif name_components[i] != "uni":
                parents_temp += name_components[i] + "/"


        self.num_classes = len(specified_class_name)
        hierarchy_format = []
        hierarchy_args = []
        hierarchy_props = []
        hierarchy_comm = []
        for ob in specified_class_name:
            format, name_args, name_props, comm = self._get_class_name_props(ob)
            hierarchy_format.append(format)
            hierarchy_args.append(name_args)
            hierarchy_props.append(name_props)
            hierarchy_comm.append(comm)

        #add parents classes to required ansible parameters
        for i in range(len(hierarchy_args)):
            arg_list = hierarchy_args[i]
            for j in range(len(arg_list)):
                arg = arg_list[j]
                details = {'comments': hierarchy_comm[i][j]}#{'hierarchy': i}
                if specified_class_name[i] == self.target_class: #naming property of target class
                    details['payload'] = hierarchy_props[i][j]
                if arg == "name":
                    details['aliases'] = [self.label]
                if iskeyword(arg):
                    details['var'] = "_" + arg
                    hierarchy_args[i][j] = details['var'] #change to new variable name to use in format string gen later
                else:
                    details['var'] = arg

                details['naming'] = True
                self.keys[arg] = details

        #create payload keys, properties in aci json payload only
        self.payload_keys = {} #target class properties only
        for key in self.keys:
            if "payload" in self.keys[key]:
                self.payload_keys[key] = self.keys[key]

        #create hierarchy instance variable
        self.hierarchy = []
        for i in range(self.num_classes):
            rn, filter = self._construct_rn_string(hierarchy_format[i],
                hierarchy_args[i], hierarchy_props[i], specified_class_name[i], unnamed_parents[i])
            self.hierarchy.append({
                              'name': specified_class_name[i],
                              'props': hierarchy_props[i],
                              'args': hierarchy_args[i],
                              'rn': rn,
                              'filter': filter
                              })
        if unnamed_target:
            self.hierarchy.append({
                              'name': self.target_class,
                              'props': [None],
                              'args': [None],
                              'rn': "\'{0}\'".format(self._get_class_name_props(self.target_class)[0]),
                              'filter': "\'\'"
                              })

    def _set_documentation(self):
        """set documentation dictionary"""

        print("Getting documentation information.")
        self.doc = {'label': self.label,
                    'name': rp['name_colon'].search(self.text).group(1),
                    'descr': rp['doc_descr'].search(self.text).group(1).strip()
                    }
                    

class ModuleGenerationException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidDNException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)

class InvalidURLException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)
