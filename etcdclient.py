import etcd3
import logging
import json


class EtcdClient:
    def __init__(self, host: str, port: int, dry_run: bool = False):
        self._dry_run = dry_run
        self._etcd = etcd3.client(host, port)
        if not self._dry_run:
            self._etcd.get('/')

    def update(self, records: dict):
        for val, meta in self._etcd.get_all():
            val = json.loads(val)
            if 'managed-by' in val and val['managed-by'] == 'skydns-register' and meta.key.decode() not in records:
                logging.info(f"Deleting {meta.key}")
                if not self._dry_run:
                    self._etcd.delete(meta.key)

        for path in records:
            record = records[path]
            logging.info(f"Putting {path}")
            if not self._dry_run:
                self._etcd.put(path, json.dumps(record))
