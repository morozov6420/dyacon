from dataclasses import dataclass
from typing import List

import pytest
from dyacon import read_config
from dyacon.read import read_yaml_to_dict, dataclass_from_dict


@pytest.mark.skip(reason='Only for local testing')
def test_read_yaml_to_dict():
    assert read_yaml_to_dict("tests/config/config0.yaml") == {
        "db": {"name": "db_name", "port": 1234}
    }


def test_read_yaml_to_dict_raise():
    with pytest.raises(ValueError, match="Config yaml file not found"):
        read_yaml_to_dict("non_existed_file.yaml")


@pytest.mark.skip(reason='Only for local testing')
def test_include():
    assert read_yaml_to_dict("tests/config/config1.yaml") == {
        "db": {"name": "db_name", "port": 1234}
    }


def test_dataclass_from_dict():
    @dataclass
    class SubClass:
        key1: str
        key2: int

    @dataclass
    class Config:
        key1: str
        key2: int
        key3: List[str]
        key4: SubClass
        key5: List[SubClass]

    assert dataclass_from_dict(
        Config,
        {
            "key1": "value1",
            "key2": 2,
            "key3": ["value3", "value4"],
            "key4": {
                "key1": "value1",
                "key2": 2,
            },
            "key5": [
                {
                    "key1": "value1",
                    "key2": 2,
                },
            ],
        },
    ) == Config(
        key1="value1",
        key2=2,
        key3=["value3", "value4"],
        key4=SubClass(key1="value1", key2=2),
        key5=[{"key1": "value1", "key2": 2}],  # noqa
        # IMPORTANT: key5 is not SubClass because it is a list of instances
        # and dataclass_from_dict can't handle it
    )


def test_dataclass_from_dict_raise():
    @dataclass
    class Config:
        key1: str
        key2: int

    with pytest.raises(TypeError, match="got an unexpected keyword argument"):
        dataclass_from_dict(
            Config,
            {
                "key1": "value1",
                "key2": 2,
                "key3": ["value3", "value4"],
            },
        )

    with pytest.raises(
        TypeError,
        match="missing 1 required positional argument",
    ):
        dataclass_from_dict(
            Config,
            {
                "key1": "value1",
            },
        )


@pytest.mark.skip(reason='Only for local testing')
def test_read_config():
    @dataclass
    class DB:
        name: str
        port: int

    @dataclass
    class Config:
        db: DB

    assert read_config(Config, "tests/config/config0.yaml") == Config(
        db=DB(
            name="db_name",
            port=1234,
        )
    )
