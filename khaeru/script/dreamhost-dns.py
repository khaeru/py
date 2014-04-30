#!/usr/bin/env python3
from functools import lru_cache
from io import TextIOWrapper
import json
import ssl
from urllib.parse import urlencode
import urllib.request
from uuid import uuid1


# Configuration for the DreamHost API
API_URI = 'https://api.dreamhost.com'
# SSL connections to api.dreamhost.com hang unless TLSv1 is used (weird…)
urllib.request.install_opener(urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))))

# Script-wide constants
DATA = {'key': None, 'format': 'json'}
DOMAIN = None


def api_call(cmd, **kwargs):
    """Invoke the DreamHost API method *cmd*."""
    data = DATA.copy()  # Populate the query data
    data.update({'unique_id': uuid1(), 'cmd': cmd}, **kwargs)
    query_uri = API_URI + '?' + urlencode(data)  # Construct query URI
    result = json.load(TextIOWrapper(urllib.request.urlopen(query_uri)))
    if result['result'] != 'success':  # Raise an exception if call failed
        raise Exception('{} failed: {}'.format(query_uri, result['result']))
    return result['data']  # Unwrap returned data


def clear(records):
    """For the {type: value} in *records*, clear DNS records for DOMAIN."""
    for t, v in records.items():
        api_call('dns-remove_record', record=DOMAIN, type=t, value=v)
        #print('Cleared {} {} {}'.format(DOMAIN, t, v))  # For debugging


def get():
    """Return a dict (possibly empty) of A, AAAA DNS records for DOMAIN."""
    result = {}
    for record in api_call('dns-list_records'):
        if record['record'] == DOMAIN and record['type'] in ['A', 'AAAA']:
            result[record['type']] = record['value']
    return result


@lru_cache()
def local_ipv4(ping='google.com'):
    """Get the local IPv4 address by opening a socket to *ping*."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((ping, 0))
    return s.getsockname()[0]


def set(addr):
    """Set the A record of DOMAIN to *addr*."""
    api_call('dns-add_record', record=DOMAIN, type='A', value=addr,
             comment='Automated update')
    #print('Set {} A {}.'.format(DOMAIN, addr))  # For debugging


if __name__ == '__main__':
    # Retrieve arguments from the command line. Optionally, edit the script
    # and set these directly above.
    if DATA['key'] is None and DOMAIN is None:
        import sys
        assert len(sys.argv) == 3, 'Must provide API key and domain arguments.'
        DATA['key'] = sys.argv[1]
        DOMAIN = sys.argv[2]
    # Perform the update
    current_records = get()
    if current_records.get('A') != local_ipv4():
        clear(current_records)
        set(local_ipv4())
    #else:  # For debugging
    #    print('Existing record is current.')
