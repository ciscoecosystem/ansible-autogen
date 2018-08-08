import re
import requests
import sys
import json

# Dictionary of Regex Patterns to pull properties from documentation html files:
rp = {  'abstract': re.compile("Class (.*?) (\(\w+\))"),
        'cleanr': re.compile("<.*?>"),
        'configurable': re.compile("Configurable: (\w+)"),
        'container_section': re.compile("<strong>Container Mos:.*?<br />", re.DOTALL),
        'contained_section': re.compile("<strong>Contained Mos:.*?<br />", re.DOTALL),
        'del':re.compile("Creatable/Deletable:\s*?([a-z]+)"),
        'dn_format': re.compile("DN FORMAT:(.*)", re.DOTALL),
        'dn_component': re.compile("(?:\w+-\{.+?\})|(?:\w+)|(?:\{.+?\})"),
        'dn_prefix_prop': re.compile("(\w+)?-?(\{\[?(\w+)\]?\})?"),
        'dn_line': re.compile("\[[0-9]*\] (.*)"),
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

class MIM:
    """
    Instance represents the Cisco ACI Management Information Model
    """

    def __init__(self, meta=None):
        """Creates dictionary containing ACI MIM information"""
        if not meta:
            self.meta = {}
        else:
            metad = json.loads(meta)
            self.meta = metad['classes']

    def get_class(self, class_name):
        if class_name not in self.meta:
            self._add_class(class_name)
        if 'dnFormat' not in self.meta[class_name]:
            self._add_dn(class_name)

        return MO(class_name, self.meta[class_name])

    def _add_dn(self, class_name):
        """Add the DNs for a specific class, only if initialized by meta file"""
        dns = []

        def add_dn_helper(class_name, dn):
            """add lists of container hierarchy"""
            containers = self.meta[class_name]['containers']
            if 'topRoot' in containers:
                dns.append(dn)
                return
            updated_dn = self.meta[class_name]['rnFormat'] + '/' + dn
            for mo in containers:
                add_dn_helper(mo, updated_dn)

        add_dn_helper(class_name, self.meta[class_name]['rnFormat'])
        self.meta[class_name]['dnFormat'] = dns

    def _add_class(self, class_name):
        """Adds class entry to self.meta; only if not initiaized by meta file"""
        r = requests.get("https://pubhub.devnetcloud.com/" + \
            "media/apic-mim-ref-311/docs/MO-{0}.html".format(class_name))
        if r.status_code != 200:
            raise InvalidURLException("class documentation request failed")
        html = r.text

        class_dict = {}
        # initiaize class attributes
        class_dict['label'] = rp['label'].search(html).group(1).strip()
        class_dict['name'] = rp['abstract'].search(html).group(1)
        class_dict['isAbstract'] = rp['abstract'].search(html).group(2) == 'ABSTRACT'
        class_dict['isConfigurable'] = rp['configurable'].search(html).group(1) == 'true'
        # class_dict['isContextRoot'] = classMeta.isContextRoot()
        class_dict['isDeletable'] = True if rp['del'].search(html).group(1) == 'yes' else False
        class_dict['help'] = rp['doc_descr'].search(html).group(1).strip()

        rn_text = rp['rn_format'].search(r.text).group(1).strip()
        rn_text = MIM._clean_html(rn_text)
        name_comp = rp['dn_component'].findall(rn_text)
        class_dict['identifiedBy'] = name_comp
        class_dict['rnFormat'] = rn_text

        # initialize properties
        all_properties = rp['prop_name'].findall(html)
        num_total = len(all_properties)
        property_doc_tags = rp['t_pre'].findall(html)[4:] # html doc corresponding to each property; first 4 always other docs, no properties

        for i in range(num_total):
            cur = all_properties[i]
            details = {}
            details['isConfigurable'] = "admin" in property_doc_tags[i] or "naming" in property_doc_tags[i]
            options = MIM._get_property_details(cur, html)
            details['options'] = options
            details['label'] = self._get_property_comments(cur, html)
            class_dict[cur] = details

        # get containment info
        contained_match = rp['contained_section'].search(html)
        if contained_match != None:
            contained_text = contained_match.group()
            contained_classes = rp['href'].findall(contained_text)
            class_dict['contains'] = {name: "" for name in contained_classes}
        else:
            class_dict['contains'] = {}

        container_match = rp['container_section'].search(html)
        if container_match != None:
            container_text = container_match.group()
            container_classes = rp['href'].findall(container_text)
            class_dict['containers'] = {name: "" for name in container_classes}
        else:
            class_dict['containers'] = {}

        # get DNs
        name_text = rp['t_pre'].search(html).group(1)
        dn_match = rp['dn_format'].search(name_text)
        dn_text = dn_match.group(1)
        class_dict['dnFormat'] = list(map(MIM._clean_html, rp['dn_line'].findall(dn_text)))

        self.meta[class_name] = class_dict

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
    def _clean_html(raw_html):
        """removes html brackets"""
        return re.sub(rp['cleanr'], "", raw_html)


class MO:
    def __init__(self, klass, meta):
        self.klass = klass
        self.meta = meta

    @property
    def properties(self):
        """
        Returns
        -------
        dict
            keys are all property names for the class
            values are dicts with keys:
                'isConfigurable': bool
                'label': str
                'options': dict - key and values are strings of option names
        """
        return self.meta['properties']

    @property
    def containers(self):
        """
        Returns
        -------
        list
            list of strings: class names of all container classes
        """
        return list(self.meta['containers'].keys())

    @property
    def contains(self):
        """
        Returns
        -------
        list
            list of strings: class names of all contained classes
        """
        return list(self.meta['contains'].keys())

    @property
    def dnFormat(self):
        """
        Returns
        -------
        list
            list of strings: all possible DN formats
        """
        return self.meta['dnFormat']


    @property
    def isAbstract(self):
        """
        Returns
        -------
        bool
            true if class is abstract
        """
        return self.meta['isAbstract']

    @property
    def isConfigurable(self):
        """
        Returns
        -------
        bool
            true if class is configurable
        """
        return self.meta['isConfigurable']

    @property
    def isDeletable(self):
        """
        Returns
        -------
        bool
            true if class is deletable
        """
        return self.meta['isDeletable']

    @property
    def label(self):
        """
        Returns
        -------
        str
            class label
        """
        return self.meta['label']

    @property
    def name(self):
        """
        Returns
        -------
        str
            package and class name separated with a colon
        """
        return self.meta['name']

    @property
    def rnFormat(self):
        """
        Returns
        -------
        str
            relative name format
        """
        return self.meta['rnFormat']

    @property
    def help(self):
        """
        Returns
        -------
        str
            class description
        """
        return self.meta['help']


class ModuleGenerationException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidDNException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)

class InvalidURLException(ModuleGenerationException):
    def __init__(self, *args, **kwargs):
        ModuleGenerationException.__init__(self,*args,**kwargs)
