#!/usr/bin/env python3

import logging
import os
import time
import argparse
import zonewalker
import recordparser
import etcdclient


def main():
    parser = argparse.ArgumentParser()
    argparse_add_environ(parser, '--zonedir', type=str, help='Directory to look for zones into')
    argparse_add_environ(parser, '--dry-run', action='store_true', default=False, help='Do not write anything to etcd')
    argparse_add_environ(parser, '--verbose', action='store_true', default=False, help='Roar out louder!')
    argparse_add_environ(parser, '--etcd-host', type=str, default='localhost', help='etcd host')
    argparse_add_environ(parser, '--etcd-port', type=int, default=2379, help='etcd port')
    argparse_add_environ(parser, '--etcd-prefix', type=str, default='external-dns', help='Prefix for etcd record keys')
    argparse_add_environ(parser, '--etcd-suffix', type=str, default='skyreg', help='Suffix for etcd record keys')
    argparse_add_environ(parser, '--loop-every', type=int, default=0, help='Loop every n seconds. Set to 0 to run once')
    argparse_add_environ(parser, '--owner-id', type=str, default='skyreg', help='ID of the owner in case more than one skydns-register is running')
    args, extra = parser.parse_known_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    while True:
        zw = zonewalker.Zonewalker()

        if args.zonedir:
            zw.load_dir(args.zonedir)

        for zonefile in extra:
            zw.load_file(zonefile)

        rp = recordparser.RecordParser(prefix=args.etcd_prefix, suffix=args.etcd_suffix)
        for z in zw.zones():
            rp.parse_zone(z)

        try:
            etcd = etcdclient.EtcdClient(args.etcd_host, int(args.etcd_port), args.dry_run, args.owner_id)
        except Exception as e:
            logging.error(f"could not connect to etcd at {args.etcd_host}:{args.etcd_port}: {str(e)}")
            exit(2)
            return

        try:
            etcd.update(rp.skydns_entries())
        except Exception as e:
            logging.error(f"error updating etcd: {str(e)}")
            exit(3)

        if args.loop_every == 0:
            break

        time.sleep(args.loop_every)


def argparse_add_environ(parser: argparse.ArgumentParser, name: str, default=None, **other):
    envdefault = os.environ.get(name.strip('-').upper().replace('-', '_'))
    parser.add_argument(name, default=(envdefault if envdefault else default), **other)


if __name__ == '__main__':
    main()
