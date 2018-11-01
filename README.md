# ACI Gen

This project is used to generate models and resources for different products which include ansible, terraform and more.

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

## How to use files generated with this module for Terraform-aci-provider ##

#### Prerequisites ####
* GO should be installed and GOPATH environment variable should be set.
* Terraform should be installed.

1. Genearte terraform files by following the above mentioned steps.
2. The terraform generator command will output 5 files for the given class name.
Files are 
    1. \<class-name>.go (Model Object for given class).
    2. \<class-name>_service.go (Service code which performs CRUD operations for given class)
    3. resource_aci_\<class-name>.go (Terraform resource file)
    4. resource-aci_\<class-name>_test.go (Terraform provider Acceptance tests for given class name)
    5. resource_aci_\<class-name>.html.markdown (Terraform resource doc file for given class name)  
3. Clone the below mentioned repositories to the location `$GOPATH/src/github.com/ciscoecosystem/` on your local machine.
    * [aci-go-client](https://github.com/ciscoecosystem/aci-go-client)
    * [Terraform-provider-aci](https://github.com/ciscoecosystem/terraform-provider-aci)

4. copy-paste the files as mentioned below.  


|                   File                 |                Location                    |
|----------------------------------------|--------------------------------------------|
|\<class-name>.go                        | `$GOPATH/src/github.com/ciscoecosystem/aci-go-client/models`                          | 
|\<class-name>_service.go                | `$GOPATH/src/github.com/ciscoecosystem/aci-go-client/client`                          | 
|resource_aci_\<class-name>.go           |`$GOPATH/src/github.com/ciscoecosystem/terraform-provider-aci/aci`                    |
|resource_aci_\<class-name>_test.go      |`$GOPATH/src/github.com/ciscoecosystem/terraform-provider-aci/aci`                    |
|resource-aci_\<class-name>.html.markdown|`$GOPATH/src/github.com/ciscoecosystem/terraform-provider-aci/website/docs/resources/`|

5. Build terraform-provider-aci using following commands.
> cd $GOPATH/erc/github.com/ciscoecosystem/terraform-provider-aci  
> make fmt  
> make build  

This will build and install the binary for terraform-provider-aci at `$GOPATH/bin`.


