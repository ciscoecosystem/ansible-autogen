# ACI Gen

This project is used to generate models and resources for different products which include ansible, terraform, RAML and more.

## Requirements ##
- Python3.6 or higher version.
- PIP3 latest version.

## HOW to install
All the required python modules used in this project are listed in requirements.txt file. To install all the required modules use pip tool as mentioned below.
```
pip install -r requirements.txt
```

## HOW to generate aci-meta.json ##
To generate the aci-meta.json file run following command.
```
python rmetagen.py -u <aci-username> -p <password> -d <host-name>
```
> Argument Reference:
  -u/--user :- ACI username.Default : admin.  
  -p/--password :- Password for the username provided.  
  -P/--port :- SSH port number. Default : 22. 
  -d/--default :- To set as default metadata.  
  \<host-name> :- Hostname of Cisco APIC.


# HOW to use

1. To Generate Ansible Modules
```
python acigen.py --ansible -m aci-meta.json -c <class-name>
```
> Argument Reference:  
  --ansible       :- To generate ansible modules.  
  -c \<class-name> :- class-name for which modules needed to be generated.  
  -m aci-meta.json :- Metadata file.  
  -l \<file-name>  :- File name which contains the list of classes for which modules are required to be generated. (Classes should be separated with new line charachter.)  
  **NOTE :-** Either of `-c` or `-l` is supported.


2. To Generate Terraform Modules
```
python acigen.py --terraform -m aci-meta.json -c <class-name>
```
> Argument Reference:  
  --terraform       :- To generate terraform modules.  
  -c \<class-name> :- class-name for which modules needed to be generated.  
  -m aci-meta.json :- Metadata file.  
  -l \<file-name>  :- File name which contains the list of classes for which modules are required to be generated. (Classes should be separated with new line charachter.)  
  **NOTE :-** Either of `-c` or `-l` is supported.


3. To Generate RAML Modules
```
python acigen.py --raml -m aci-meta.json -c <class-name>
```
> Argument Reference:  
  --raml           :- To generate raml modules.  
  -c \<class-name> :- class-name for which modules needed to be generated.  
  -m aci-meta.json :- Metadata file.  
  -l \<file-name>  :- File name which contains the list of classes for which modules are required to be generated. (Classes should be separated with new line charachter.)  
  **NOTE :-** Either of `-c` or `-l` is supported.

> **NOTE :-**
   * Change the credentials in **raml_generator/config.py** file as per the user account before running above command.
   * All the generated raml modules will be present in **raml_generator/gen/cisco_aci**.
   * All the script related logs can be found in **aci_raml.log**.