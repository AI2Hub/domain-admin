# -*- coding: utf-8 -*-
"""
@File    : cert_util.py
@Date    : 2022-10-22
@Author  : Peng Shiyu

通过socket 获取域名ssl 证书信息

参考：
Python脚本批量检查SSL证书过期时间
https://linuxeye.com/479.html
"""

import json
import socket
import ssl

from dateutil import parser

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# SSL默认端口
SSL_DEFAULT_PORT = 443

DEFAULT_SOCKET_TIMEOUT = 5


def create_ssl_context():
    """
    优先返回不校验证书的上下文
    :return:
    """
    try:
        return ssl._create_unverified_context(check_hostname=True)
    except AttributeError:
        pass

    return ssl.create_default_context()


def get_domain_cert(host, port=SSL_DEFAULT_PORT):
    """
    获取证书信息
    :param host: str
    :param port: int
    :return: dict
    """
    context = create_ssl_context()

    with socket.create_connection(address=(host, port), timeout=DEFAULT_SOCKET_TIMEOUT) as sock:
        with context.wrap_socket(sock, server_hostname=host) as wrap_socket:
            return wrap_socket.getpeercert()


def parse_domain_with_port(domain_with_port):
    """
    解析域名，允许携带端口号
    :param domain_with_port: str
        例如：
        www.domain.com
        www.domain.com:8888
    :return: dict
    """
    if ':' in domain_with_port:
        domain, port = domain_with_port.split(':')
    else:
        domain = domain_with_port
        port = SSL_DEFAULT_PORT

    if not isinstance(port, int):
        port = int(port)

    return {
        'domain': domain,
        'port': port,
    }


def get_domain_ip(domain):
    """
    获取ip地址
    :param domain: str
    :return: str
    """
    return socket.gethostbyname(domain)


def get_cert_info(domain_with_port):
    """
    获取证书信息
    :param domain_with_port: str
    :return: dict
    """
    domain_info = parse_domain_with_port(domain_with_port)
    domain = domain_info.get('domain')
    port = domain_info.get('port', SSL_DEFAULT_PORT)

    cert = get_domain_cert(domain, port)

    issuer = _tuple_to_dict(cert['issuer'])
    subject = _tuple_to_dict(cert['subject'])

    return {
        'domain': domain_with_port,
        'ip': get_domain_ip(domain),
        'subject': _name_convert(subject),
        'issuer': _name_convert(issuer),
        # 'version': cert['version'],
        # 'serial_number': cert['serialNumber'],
        'start_date': _parse_time(cert['notBefore']),
        'expire_date': _parse_time(cert['notAfter']),
    }


def _tuple_to_dict(cert_tuple):
    """
    cert证书 tuple转dict
    :param cert_tuple: tuple
    :return:
    """
    data = {}
    for item in cert_tuple:
        data[item[0][0]] = item[0][1]

    return data


def _name_convert(data):
    """
    名字转换
    :param data: dict
    :return: dict
    """
    name_map = {
        'C': 'countryName',
        'CN': 'commonName',
        'O': 'organizationName',
        'OU': 'organizationalUnitName',
        'L': 'localityName',
        'ST': 'stateOrProvinceName'
    }

    dct = {}
    for key, value in name_map.items():
        dct[key] = data.get(value, '')

    return dct


def _parse_time(time_str):
    """
    解析并格式化时间
    :param time_str: str
    :return: str
    """
    return parser.parse(time_str).astimezone().strftime(DATETIME_FORMAT)
