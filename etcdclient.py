import etcd3
import logging


class EtcdClient:
    def __init__(self, host: str, port: int, dry_run: bool = False):
        self._dry_run = dry_run
        self._etcd = etcd3.client(host, port)
        if not self._dry_run:
            self._etcd.get('')

    def update(self, records: dict):
        for oldk, oldv in self._etcd.get_all():
            if 'managed-by' in oldv and oldv['managed-by'] == 'skydns-register' and oldk not in records:
                logging.info(f"Deleting {oldk}")
                if not self._dry_run:
                    self._etcd.delete(oldk)

        for path in records:
            record = records['key']
            logging.info(f"Putting {path}")
            if not self._dry_run:
                self._etcd.put(path, record)
