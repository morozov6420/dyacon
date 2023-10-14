import os
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern


class Loader(ABC):
    @property
    @abstractmethod
    def pattern(self) -> Pattern[str]:
        raise NotImplementedError

    @abstractmethod
    def load(self, config_content: str) -> str:
        raise NotImplementedError


ENV_LOADER_PATTERN = re.compile(
    r'\${'
    r'(?P<name>[^}^{:]+)'
    r'(?P<separator>:?)'
    r'(?P<default>.*?)'
    r'}'
)


class EnvLoader(Loader):
    def __init__(self) -> None:
        self._pattern = ENV_LOADER_PATTERN

    @property
    def pattern(self) -> Pattern[str]:
        return self._pattern

    def load(self, config_content: str) -> str:
        findings = list(self.pattern.finditer(config_content))

        for match in reversed(findings):
            env_name = match.group('name')
            has_default = match.group('separator') == ':'

            value = os.getenv(env_name)

            if value is None:
                if not has_default:
                    raise ValueError(
                        f'Missing required environment variable {env_name}'
                    )
                value = match.group('default')
            span_min, span_max = match.span()
            config_content = (
                f'{config_content[:span_min]}'
                f'{value}'
                f'{config_content[span_max:]}'
            )
        return config_content


class Load:
    def __init__(self, loaders: Optional[List[Loader]] = None) -> None:
        self.loaders = [EnvLoader()]
        if loaders:
            self.loaders.extend(loaders)

    def load(self, config_content: str) -> str:
        for loader in self.loaders:
            if list(loader.pattern.finditer(config_content)):
                return loader.load(config_content)
        return config_content

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.load(value)
