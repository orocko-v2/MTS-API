import json

import requests
from Exceptions import FlagDoesNotExistsException

""" token to authorize"""
global token

""" types of requests allowed by MTS API"""
tuple = (
    'BALANCE_BY_MSISDN',
    # https://developers.mts.ru/mts-business-api/documentation/31-zapros-informatsii-o-balanse-po-nomeru
    'BALANCE_BY_ACCOUNT',
    # https://developers.mts.ru/mts-business-api/documentation/32-zapros-informatsii-o-balanse-po-litsevomu-schetu
    'INFO_BY_MSISDN',
    # https://developers.mts.ru/mts-business-api/documentation/105-poluchenie-informatsii-po-zadannomu-msisdn
    'BILLS_BY_MSISDN',
    # https://developers.mts.ru/mts-business-api/documentation/33-detalizatsiya-za-period-po-nomeru-telefona
    'EXT_BILLS_BY_MSISDN',
    # https://developers.mts.ru/mts-business-api/documentation/35-detalizatsiya-za-period-po-nomeru-telefona-rasshirennaya
    'CHARGES_BY_MSISDN',
    # https://developers.mts.ru/mts-business-api/documentation/38-zapros-spiska-nachislenii-po-nomeru-telefona

)

def getAccessToken(*args):
    """
    Creates request to get access token
    :param args: login and password (if user enters it) or empty (if it's contained in json file)
    :return: access_token
    """
    if len(args) == 0:  # getting login/password from json file
        file = open("data/auth-params.json")
        auth_params = json.load(file)
        login = auth_params.get('login')
        password = auth_params.get('password')
        data = {'grant_type': 'client_credentials'}
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        resp = requests.post(url='https://api.mts.ru/token', auth=(login, password), data=data, headers=header)
        if resp.status_code != requests.codes.ok:
            resp.raise_for_status()
        file.close()
        return resp.json()['access_token']
    elif len(args) == 2:  # getting login/password from user
        data = {'grant_type': 'client_credentials'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        login = args[0]
        password = args[1]
        resp = requests.post(url='https://api.mts.ru/token', auth=(login, password), data=data, headers=headers)
        if resp.status_code != requests.codes.ok:
            resp.raise_for_status()
        return resp.json()['access_token']
    else:
        raise TypeError(f"getAccessToken takes 0 or 2 positional arguments but {len(args)} were given")


def createsSimpleRequest(method, url, params, headers):
    """
    Function allows to create request
    :param method: HTTP-method
    :param url: URL
    :param params: data for "post" requests or params for "get" (dictionary)
    :param headers: most of the time "Authorization" header
    :return: response
    """
    match method:
        case "get":
            resp = requests.get(url=url, params=params, headers=headers)
            if resp.status_code != requests.codes.ok:
                resp.raise_for_status()
            return resp

        case "post":
            resp = requests.post(url=url, data=params, headers=headers)
            if resp.status_code != requests.codes.ok:
                resp.raise_for_status()
            return resp


def createHeaders(token):
    """
    Creates header with authorization field
    :param token: access token
    :return: dictionary
    """
    return {"Authorization": f"Bearer {token}"}


def createRequest(flag, params_list):
    """
    Creates request of current type
    :param flag: type of request
    :param params_list: data
    :return: responce
    """
    global url, data, type
    if not tuple.__contains__(flag):
        raise FlagDoesNotExistsException(flag)
    match flag:
        case 'BALANCE_BY_MSISDN':
            type = 'get'
            url = 'https://api.mts.ru/b2b/v1/Bills/CheckBalanceByMSISDN'
            data = {'characteristic.value': params_list[0]}
        case 'BALANCE_BY_ACCOUNT':
            type = 'get'
            url = 'https://api.mts.ru/b2b/v1/Bills/CheckBalanceByAccount'
            data = {'accountNo': params_list[0]}
        case 'INFO_BY_MSISDN':
            type = 'get'
            url = 'https://api.mts.ru/b2b/v1/Service/HierarchyStructure'
            data = {'msisdn': params_list[0]}
        case 'BILLS_BY_MSISDN':
            type = 'get'
            url = 'https://api.mts.ru/b2b/v1/Bills/BillingStatementByMSISDN'
            data = {'msisdn': params_list[0], 'startDateTime': params_list[1], 'endDateTime': params_list[2]}
        case 'EXT_BILLS_BY_MSISDN':
            type = 'get'
            url = 'https://api.mts.ru/b2b/v1/Bills/BillingStatementExtdByMSISDN'
            data = {'msisdn': params_list[0], 'startDateTime': params_list[1], 'endDateTime': params_list[2]}
        case 'CHARGES_BY_MSISDN':
            type = 'post'
            url = 'https://api.mts.ru/b2b/v1/Bills/CheckCharges'
            data = {'id': params_list[0]}

    return createsSimpleRequest(type, url, data, createHeaders(token))
