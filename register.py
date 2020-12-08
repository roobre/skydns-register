#!/usr/bin/env python3

import yaml
import json
import os
import argparse
import etcd3


def main():
    parser = argparse.ArgumentParser()
    argparse_add_environ(parser, '--etcd-host', type=str, default='localhost', help='URI for etcd host')
    argparse_add_environ(parser, '--etcd-port', type=int, default=2379, help='URI for etcd host')
    argparse_add_environ(parser, '--etcd-prefix', type=str, default='external-dns',
                         help='Directory to look for zones into')
    argparse_add_environ(parser, '--zonedir', type=str, help='Directory to look for zones into')
    args, extra = parser.parse_known_args()

    zones = []
    if args.zonedir:
        for zonefile in os.scandir(args.zonedir):
            if zonefile.is_file() and (zonefile.path.endswith('.yaml') or zonefile.path.endswith('.yml')):
                zones.append(load_yaml_zone(os.path.join(args.zonedir, zonefile.name)))

    for zonefile in extra:
        zones.append(load_yaml_zone(zonefile))

    etcd = etcd3.client(host=args.etcd_host, port=args.etcd_port)

    records = {}
    for z in zones:
        records.update(sky_from_zone(z))

    for r in records:
        print(f"Registering{r}...")
        etcd.put(r, records[r])
    print("Done, have a nice day!")


def argparse_add_environ(parser: argparse.ArgumentParser, name: str, default: str = '', **other):
    envdefault = os.environ.get(name.strip('-').upper().replace('-', '_'))
    parser.add_argument(name, default=(envdefault if envdefault else default), nargs='?', **other)


def load_yaml_zone(filepath):
    file = open(filepath, mode='r')
    contents = yaml.safe_load(file)
    file.close()

    return contents


def sky_from_zone(zone: dict, prefix: str = '') -> dict:
    if prefix != "":
        prefix = prefix.strip('/') + '/'
    basepath = '/' + prefix + dot_to_slashes(zone['zone'])

    skyrecords = {}
    for rk in dict(zone['records']):
        records = zone['records'][rk]

        if type(records) != list:
            records = [records]

        for record in records:
            skykey = basepath
            if rk != '':
                skykey += f"/{dot_to_slashes(rk)}"

            if record['type'] == 'MX':
                skyrecords[skykey]['mail'] = True
                continue

            value = ''
            if 'value' in record:
                value = record['value']
            if 'values' in record and len(record['values']) > 0:
                value = record['values'][0]

            if value == '':
                raise Exception(f"Could not find value for record '{rk}'")

            skyrecord = None
            if record['type'] in ['CNAME', 'A', 'AAAA']:
                skyrecord = {
                    "host": value,
                    "text": "github.com/roobre/skydns-register"
                }
            elif record['type'] == 'TXT':
                skyrecord = {
                    "text": value
                }
            else:
                raise Exception(f"Unsupported type'{record['type']}'")

            if skykey not in skyrecords:
                skyrecords[skykey] = skyrecord

    return skyrecords


def dot_to_slashes(dotname: str) -> str:
    pieces = dotname.split('.')
    pieces.reverse()
    return '/'.join(pieces)


if __name__ == '__main__':
    main()
