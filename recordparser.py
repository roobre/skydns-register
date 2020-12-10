import logging

from typing import Dict


class RecordParser:
    def __init__(self, prefix: str = ''):
        self._records: Dict[Record] = {}
        self._prefix = prefix

    def parse_zone(self, zone: dict):
        zonename = zone['zone']
        for rname in zone['records']:
            record = zone['records'][rname]

            if rname == '*':
                logging.warning(f"Wilcard name ('*') is not supported in skydns, skipping")
                continue

            key = self._dots_to_slashes(f"{rname}.{zonename}")
            self._records[key] = Record(rname, record)

    def skydns_entries(self) -> dict:
        skyentries = {}
        for key in self._records:
            record = self._records[key]
            try:
                skyrecord = record.skydns()
                skyentries[key] = skyrecord
            except Exception as e:
                logging.error(f"error converting record {key}: {str(e)}")

        return skyentries

    def _dots_to_slashes(self, dotname: str) -> str:
        prefix = '/' + self._prefix
        pieces = dotname.strip('.').split('.')
        pieces.append('')
        pieces.reverse()
        return prefix + '/'.join(pieces)


class Record:
    def __init__(self, name: str, entries: [dict, list]):
        if type(entries) != list:
            entries = [entries]

        self._entries = entries
        self._name = name

    """
    Convert record to skydns format
    """

    def skydns(self) -> dict:
        record = {
            "managed-by": "skydns-register",
        }

        for entry in self._entries:
            if 'type' not in entry:
                logging.warning(f"missing attribute 'type' for value in {self._name}, skipping")
                continue

            if entry['type'] == 'MX':
                record['mail'] = True
                continue

            if 'value' not in entry:
                if 'values' in entry and type(entry['values']) == list and len(entry['values']) > 0:
                    logging.info(f"Using first entry of 'values' as value for '{self._name}'")
                    entry['value'] = entry['values'][0]
                else:
                    logging.warning(f"entry {self._name} lacks both 'value' and 'values[]', skipping")
                    continue

            if entry['type'] in ['A', 'AAAA', 'CNAME']:
                record['host'] = entry['value']
            elif entry['type'] == 'TXT':
                record['text'] = entry['value']

        if 'mail' in record and 'host' not in record:
            raise Exception("Record has MX type but not an address associated to it")

        return record
