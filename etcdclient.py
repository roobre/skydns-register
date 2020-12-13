import etcd3
import logging
import json


class EtcdClient:
    def __init__(self, host: str, port: int, dry_run: bool = False, owner_id: str = 'skyreg'):
        self._owner_id = owner_id
        self._dry_run = dry_run
        self._etcd = etcd3.client(host, port)
        if not self._dry_run:
            self._etcd.get('/')

    def update(self, records: dict):
        for val, meta in self._etcd.get_all():
            val = json.loads(val)
            if 'managed-by' in val and val['managed-by'] == self._owner_id and meta.key.decode() not in records:
                logging.info(f"Deleting {meta.key}")
                if not self._dry_run:
                    self._etcd.delete(meta.key)

        for path in records:
            record = records[path]
            record['managed-by'] = self._owner_id
            logging.info(f"Putting {path}")
            if not self._dry_run:
                self._etcd.put(path, json.dumps(record))
