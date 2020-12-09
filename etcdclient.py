import etcd3
import logging


class EtcdClient:
    def __init__(self, host: str, port: int):
        self._etcd = etcd3.client(host, port)
        self._etcd.get('')

    def update(self, records: dict):
        for oldk, oldv in self._etcd.get_all():
            if 'managed-by' in oldv and oldv['managed-by'] == 'skydns-register' and oldk not in records:
                logging.info(f"Deleting {oldk}")
                self._etcd.delete(oldk)

        for path in records:
            record = records['key']
            logging.info(f"Putting {path}")
            self._etcd.put(path, record)
