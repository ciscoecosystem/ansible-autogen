import json
import requests

from config import *
from exception_handler import handle_exception


@handle_exception
def get_localhost_data(port):
    """
    gets the data on localhost

    it requests the data on localhost whose
    port number is stored in 'port'

    Parameters
    ----------
    port : string
        port number of localhost whose data will
        be requested
    Returns
    -------
    data : dictionary
        requested localhost data
    """
    response = requests.get(
        'http://localhost:{}/'.format(port), timeout=30)
    return response


@handle_exception
def get_aci_cookie(base_url=APIC_BASE_URL, password=APIC_PASSWORD, username=APIC_USERNAME):
    """
    returns aci cookie

    gets the token by logging into cisco apic and
    generates the aci cookie for subsequent requests

    Parameters
    ----------
    base_url : string
        Cisco APIC base url for all cisco requests
    password : string
        Cisco APIC password
    username : string
        Cisco APIC username
    Returns
    -------
    cookie : dict
        apic cookie for subsequent cisco apic requests
    """
    login_url = '{}/api/aaaLogin.json'.format(base_url)
    data = {'aaaUser': {'attributes': {
        'pwd': password, 'name': username}}}
    data = json.dumps(data)
    response = requests.post(login_url, data=data,
                             verify=False, timeout=30)
    response.raise_for_status()
    response = response.json()
    cookie = {'APIC-Cookie': response['imdata']
              [0]['aaaLogin']['attributes']['token']}

    return cookie


@handle_exception
def get_aci_data(class_name, base_url=APIC_BASE_URL):
    """
    gets the data of aci class from Cisco APIC

    gets the data of aci class ('class_name') from
    Cisco APIC

    Parameters
    ----------
    class_name : string
        aci class whose data needs to be requested
        from Cisco APIC
    base_url : string
        Cisco APIC base url for all cisco requests
    Returns
    -------
    response : request object
        requested data of aci class from Cisco APIC
    """
    cookie = get_aci_cookie()
    class_url = '{}/api/node/class/{}.json'.format(base_url, class_name)
    response = requests.get(class_url, cookies=cookie,
                            verify=False, timeout=30)
    response.raise_for_status()
    return response
