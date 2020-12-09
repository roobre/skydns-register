import yaml
import logging
import os


class Zonewalker:
    def __init__(self):
        self._zones = []

    def load_dir(self, path: str):
        for zonefile in os.scandir(path):
            if zonefile.is_file() and (zonefile.path.endswith('.yaml') or zonefile.path.endswith('.yml')):
                self.load_file(os.path.join(path, zonefile.name))

    def load_file(self, yaml_path: str):
        try:
            zone = self._yaml_load(yaml_path)
        except Exception as e:
            logging.warning(f"skipping zone from {yaml_path}: {str(e)}")
            return

        self._zones.append(zone)

    def zones(self) -> list:
        return self._zones

    @staticmethod
    def _yaml_load(filepath: str):
        file = open(filepath, mode='r')
        contents = yaml.safe_load(file)
        file.close()

        Zonewalker._validate(contents)

        return contents

    @staticmethod
    def _validate(zone: dict):
        if type(zone) != dict:
            raise Exception("zone is not a dict")
        if 'zone' not in zone or type(zone['zone']) != str:
            raise Exception("zone.zone must exist and be a string")
        if 'records' not in zone or type(zone['records']) != dict or len(zone['records']) <= 0:
            raise Exception("invalid record list")
