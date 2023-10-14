from dataclasses import dataclass
from unittest.mock import patch

import pytest
from dyacon import Load
from dyacon.read import dataclass_from_dict
from dyacon.loaders.external import GoogleLoad


def test_env_loader():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': '${ENV1}'}

    with patch('os.getenv', return_value='value1'):
        assert dataclass_from_dict(Config, config_dict) == Config('value1')


def test_env_loader_raise():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': '${ENV1}'}

    with patch('os.getenv', return_value=None):
        with pytest.raises(
            ValueError,
            match='Missing required environment variable ENV1',
        ):
            dataclass_from_dict(Config, config_dict)


def test_env_loader_default_value():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': '${ENV1:default}'}

    with patch('os.getenv', return_value=None):
        assert dataclass_from_dict(Config, config_dict) == Config('default')


def test_env_loader_several_groups():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': 'hello-${ENV1}${ENV2}'}

    with patch.dict('os.environ', {'ENV1': 'value1', 'ENV2': 'value2'}):
        assert dataclass_from_dict(Config, config_dict) == Config(
            'hello-value1value2'
        )


def test_google_loader_default():
    @dataclass
    class Config:
        key1: str = GoogleLoad()

    config_dict = {'key1': '!{secret_name:project_id:default}'}

    assert dataclass_from_dict(Config, config_dict) == Config('default')


def test_google_loader_without_default():
    @dataclass
    class Config:
        key1: str = GoogleLoad()

    config_dict = {'key1': '!{secret_name:project_id}'}

    with pytest.raises(
        ValueError,
        match='Missing required google cloud secret manager',
    ):
        dataclass_from_dict(Config, config_dict)
