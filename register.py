#!/usr/bin/env python3

import logging
import os
import argparse
import zonewalker
import recordparser
import etcdclient


def main():
    parser = argparse.ArgumentParser()
    argparse_add_environ(parser, '--zonedir', type=str, help='Directory to look for zones into')
    argparse_add_environ(parser, '--etcd-host', type=str, default='localhost', help='URI for etcd host')
    argparse_add_environ(parser, '--etcd-port', type=int, default=2379, help='URI for etcd host')
    argparse_add_environ(parser, '--etcd-prefix', type=str, default='external-dns', help='Prefix for etcd record keys')
    args, extra = parser.parse_known_args()

    zw = zonewalker.Zonewalker()

    if args.zonedir:
        zw.load_dir(args.zonedir)

    for zonefile in extra:
        zw.load_file(zonefile)

    rp = recordparser.RecordParser(prefix=args.etcd_prefix)
    for z in zw.zones():
        rp.parse_zone(z)

    try:
        etcd = etcdclient.EtcdClient(args.etcd_host, int(args.etcd_port))
    except Exception as e:
        logging.error(f"could not connect to etcd at {args.etcd_host}:{args.etcd_port}: {str(e)}")
        exit(2)
        return

    etcd.update(rp.skydns_entries())


def argparse_add_environ(parser: argparse.ArgumentParser, name: str, default: str = '', **other):
    envdefault = os.environ.get(name.strip('-').upper().replace('-', '_'))
    parser.add_argument(name, default=(envdefault if envdefault else default), nargs='?', **other)


if __name__ == '__main__':
    main()
