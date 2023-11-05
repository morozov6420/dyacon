from dataclasses import dataclass
from unittest.mock import patch

import pytest
from dyacon import Load
from dyacon.loaders.external import GoogleCloudSecretLoader
from dyacon.loaders.external.google import SecretManagerServiceClient
from dyacon.read import dataclass_from_dict


def test_env_loader():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': '${ENV1}'}

    with patch('os.getenv', return_value='value1'):
        assert dataclass_from_dict(Config, config_dict).key1 == 'value1'


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
        assert dataclass_from_dict(Config, config_dict).key1 == 'default'


def test_env_loader_several_groups():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {'key1': 'hello-${ENV1}${ENV2}'}

    with patch.dict('os.environ', {'ENV1': 'value1', 'ENV2': 'value2'}):
        assert dataclass_from_dict(Config, config_dict).key1 == (
            'hello-value1value2'
        )


@pytest.mark.skipif(
    SecretManagerServiceClient is not None,
    reason=(
        'google-cloud-secret-manager is installed, '
        'but secret_name and project_id are not real'
    ),
)
def test_google_loader_default():
    @dataclass
    class Config:
        key1: str = Load([GoogleCloudSecretLoader()])

    config_dict = {'key1': '!{secret_name:project_id:default}'}

    assert dataclass_from_dict(Config, config_dict).key1 == 'default'


@pytest.mark.skipif(
    SecretManagerServiceClient is not None,
    reason=(
        'google-cloud-secret-manager is installed, '
        'but secret_name and project_id are not real'
    ),
)
def test_google_loader_without_default():
    @dataclass
    class Config:
        key1: str = Load([GoogleCloudSecretLoader()])

    config_dict = {'key1': '!{secret_name:project_id}'}

    with pytest.raises(
        ValueError,
        match='Missing required google cloud secret manager',
    ):
        dataclass_from_dict(Config, config_dict)


def test_not_required():
    @dataclass
    class Config:
        key1: str = Load()

    config_dict = {}

    assert dataclass_from_dict(Config, config_dict).key1 is None


def test_required():
    @dataclass
    class Config:
        key1: str = Load(required=True)

    config_dict = {}

    with pytest.raises(ValueError, match='key1 field cannot be empty'):
        dataclass_from_dict(Config, config_dict)


def test_default():
    @dataclass
    class Config:
        key1: str = Load(default='default')

    config_dict = {}

    assert dataclass_from_dict(Config, config_dict).key1 == 'default'


def test_default_factory():
    @dataclass
    class Config:
        key1: str = Load(default_factory=lambda: 'default')

    config_dict = {}

    assert dataclass_from_dict(Config, config_dict).key1 == 'default'
