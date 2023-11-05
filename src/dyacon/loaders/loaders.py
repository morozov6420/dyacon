import os
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern, Callable, Any


class Loader(ABC):
    @property
    @abstractmethod
    def pattern(self) -> Pattern[str]:
        raise NotImplementedError

    @abstractmethod
    def load(self, config_content: str) -> str:
        raise NotImplementedError


# fmt: off
ENV_LOADER_PATTERN = re.compile(
    r'\${'
    r'(?P<name>[^}^{:]+)'
    r'(?P<separator>:?)'
    r'(?P<default>.*?)'
    r'}'
)
# fmt: on


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
    """
    for extending just inherit from this class and override __init__ method
    or use lambda function
    examples:
    >>> MyLoad1 = lambda: Load(loaders=[MyLoader()])
    >>> class MyLoad2(Load):
    ...     def __init__(
    ...          self,
    ...          loaders: Optional[List[Loader]] = None,
    ...          *,
    ...          default: Optional[str] = None,
    ...          default_factory: Optional[Callable[[], Any]] = None,
    ...          required: bool = False,
    ...      ) -> None:
    ...          super().__init__(
    ...              loaders,
    ...              default=default,
    ...              default_factory=default_factory,
    ...              required=required,
    ...          )
    ...          self.loaders.append(MyLoader())  # <-- here is your new loader
    """

    def __init__(
        self,
        loaders: Optional[List[Loader]] = None,
        *,
        default: Optional[str] = None,
        default_factory: Optional[Callable[[], Any]] = None,
        required: bool = False,
    ) -> None:
        self.loaders = [EnvLoader()]
        self.required = required
        self.default = default
        self.default_factory = default_factory
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
        if self is not value:
            instance.__dict__[self.name] = self.load(value)
        else:
            if self.required:
                raise ValueError(f'{self.name} field cannot be empty')
            if self.default_factory:
                instance.__dict__[self.name] = self.default_factory()
            else:
                instance.__dict__[self.name] = self.default
