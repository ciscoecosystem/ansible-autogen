#!/usr/bin/env python

from __future__ import print_function
from scp import SCPClient
import argparse
import getpass
import inspect
import os
import paramiko
import errno


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate pyaci meta from APIC')

    parser.add_argument('host', nargs=1,
                        help='hostname of APIC')
    parser.add_argument('-P', '--port', type=int, default=22,
                        help='SSH port of APIC')

    parser.add_argument('-u', '--user', type=str, default='admin',
                        help='authentication username')
    parser.add_argument('-p', '--password', type=str,
                        help='authentication password')

    parser.add_argument('-d', '--default', action='store_true',
                        help='set as default meta')

    args = parser.parse_args()

    if args.password is None:
        args.password = getpass.getpass('Enter {} password for {}: '.format(
            args.user, args.host[0]))

    return args


def main():
    args = parse_args()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host[0], port=args.port, username=args.user,
                password=args.password, allow_agent=False,
                look_for_keys=False)
    stdin, stdout, stderr = ssh.exec_command('acidiag version')
    version = ''.join(stdout.readlines()).strip()
    vlist = version.split('.')
    version = '{}.{}({})'.format(vlist[0], vlist[1], '.'.join(vlist[2:]))
    print('APIC is running version', version)

    print('Copying metagen.py to APIC')
    scp = SCPClient(ssh.get_transport())
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    script_dir = os.path.dirname(os.path.abspath(filename))
    metagen_path = os.path.join(script_dir, 'metagen.py')
    scp.put(metagen_path, '/tmp/metagen.py')

    print('Invoking metagen.py on APIC')
    stdin, stdout, stderr = ssh.exec_command('python2.7 /tmp/metagen.py')
    ''.join(stdout.readlines()).strip()
    # TODO (2015-09-14, Praveen Kumar): Check the exit status properly.

    destination = os.getcwd() + "/aci-meta.json"
    print('Copying generated meta from APIC to', destination)
    scp.get('aci-meta.json', destination)


if __name__ == '__main__':
    main()
