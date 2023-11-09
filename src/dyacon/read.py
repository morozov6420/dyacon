import os
from dataclasses import fields
from typing import Dict, Type, TypeVar

import yaml
from dotenv import find_dotenv

T = TypeVar('T')


def read_config(klass: Type[T], path: str = 'config/config.yaml') -> T:
    config_dict = read_yaml_to_dict(path)
    dataclass_instance = dataclass_from_dict(klass, config_dict)
    return dataclass_instance


def read_yaml_to_dict(path: str = 'config/config.yaml') -> Dict:
    # TODO: add exception or warning for non-dict structures?
    config_abs_path = find_dotenv(path)
    if not config_abs_path and not os.path.isfile(path):
        raise ValueError(f'Config yaml file not found on path: {path}')

    class Loader(yaml.SafeLoader):
        def __init__(self, stream):
            self._root = os.path.split(stream.name)[0]
            super().__init__(stream)

        def include(self, node):
            filename = os.path.join(self._root, self.construct_scalar(node))
            with open(filename, 'r') as file:
                return yaml.load(file, Loader)

    Loader.add_constructor('!include', Loader.include)

    with open(config_abs_path or path, 'r') as f:
        config_dict: Dict = yaml.load(f, Loader=Loader)
    return config_dict


def dataclass_from_dict(klass: Type[T], d: Dict) -> T:
    # TODO: add exceptions or warnings for container types&
    #  they work, but descriptor loaders.loaders.Load() is not working for
    #  items of list
    #  may be I should use dacite lib, idk, but it looks
    #  overcomplicated in configuration context
    #  #
    #  example of config.yaml:
    #  field: "${PATH}" # Load() is working, value of env var PATH will be here
    #  lst:
    #    - key: "${secret1}" # Load() is not working
    #    - "${secret2}" # Load() is not working
    #  #
    #  result will be just yaml values without loading from env:
    #  {"field": <PATH value>, "lst": [{"key": "${secret1}"}, "${secret2}"]}
    try:
        field_types = {field.name: field.type for field in fields(klass)}
        key_value = {}
        for key, value in d.items():
            try:
                key_value[key] = dataclass_from_dict(field_types[key], value)
            except KeyError as _:
                key_value[key] = value
        return klass(**key_value)
    except TypeError as e:
        if 'must be called with a dataclass type or instance' in str(e):
            return d
        raise e
