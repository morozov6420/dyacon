English version: [README.md](README.md)

# Dyacon

Dyacon - это библиотека для работы с конфигурациями в формате YAML в Python. Она предоставляет инструменты для удобной загрузки и обработки конфигураций, а также поддерживает загрузку значений из переменных окружения и других источников, таких как Google Secret Manager. 

Использование нескольких конфигурационных файлов позволяет хранить сразу же несколько настроек для одного сервиса и легко их подменять для различных целей, например, для тестирования или дебага.

## Установка

Вы можете установить `dyacon` с помощью pip:

```shell
pip install dyacon
```

Если вы хотите использовать поддержку Google Secret Manager, установите библиотеку с соответствующими опциями и установите переменную окружения `GOOGLE_APPLICATION_CREDENTIALS` с путем к файлу сервисного аккаунта Google Cloud:

```shell
pip install "dyacon[google]"
```

## Зачем использовать Dyacon?

Библиотека Dyacon предназначена для упрощения работы с конфигурациями в формате YAML в ваших Python-приложениях. Она предлагает следующие возможности:

- **Сбор нескольких YAML-файлов в один**: Dyacon позволяет вам создавать иерархию конфигураций, собирая данные из нескольких файлов. Это удобно для разделения конфигурации на различные файлы и компоненты. Более подробно читайте в разделе [Загрузка конфигурации](#загрузка-конфигурации).

- **Загрузка значений из переменных окружения**: Dyacon позволяет вам включать значения из переменных окружения в вашу конфигурацию. Вы можете использовать специальный синтаксис `${env_variable_name:default_value}`, чтобы задать имя искомой переменной окружения и значение по умолчанию.
  ```yaml
  # config/config.yaml
  token: "${API_TOKEN:default_value}" 
  ```

  ```python
  # config.py
  from dataclasses import dataclass
  from dyacon import read_config, Load

  @dataclass
  class Config:
      token: str = Load()

  config = read_config(Config)
  ```

- **Загрузка значений из Google Secret Manager**: Если вы работаете в облаке Google Cloud, Dyacon предоставляет загрузчик для Google Secret Manager. Вы можете загружать конфиденциальные данные, такие как пароли и ключи, из Secret Manager с использованием синтаксиса `${env_variable_name:project_id:default_value}`.
  ```yaml
  # config/config.yaml
  token: "${API_TOKEN:my-project:default_value}" 
  ```

  ```python
  # config.py
  from dataclasses import dataclass
  from dyacon import read_config, Load
  from dyacon.loaders.external import GoogleCloudSecretLoader

  @dataclass
  class Config:
      token: str = Load([GoogleCloudSecretLoader()])

  config = read_config(Config)
  ```

## Использование

### Загрузка конфигурации

Dyacon предоставляет инструменты для загрузки конфигурации из YAML-файла и преобразования ее в Python-объекты. Должен быть создан целевой файл конфигурации, в которой, при необходимости, будут включены другие файлы. Например, в примере ниже, файл `config/config.yaml` включает файл `db/local.yaml`. Если мы захотим использовать настройки для продового окружения, мы можем создать файл с другим именем, например, `db/prod.yaml` и включить его в `config/config.yaml` с помощью директивы `!include db/prod.yaml`. Путь в директиве `!include` должен быть относительным к файлу, в котором она используется. 

В итоге, нам бы просто пришлось поменять одну строку в файле конфигурации, чтобы переключиться на другие настройки.

```yaml
# config/config.yaml
db: !include db/local.yaml
```

```yaml
# config/db/local.yaml
host: localhost
port: 3306
name: local_db
```

```python
# config.py
from dataclasses import dataclass
from dyacon import read_config

@dataclass
class DbConfig:
    host: str
    port: int
    name: str

@dataclass
class Config:
    db: DbConfig

config = read_config(Config)
print(config.db.host) # localhost
```

Функция `read_config` принимает опциональный аргумент `path`, который указывает на загружаемый целевой YAML-файл. Если аргумент не указан, Dyacon будет искать файл `config/config.yaml` относительно текущей директории.

### Дескриптор Load

Дескриптор `Load`, который позволяет вам внедрять автоматическую загрузку значений конфигурации из различных источников. `Load` принимает список загрузчиков, которые будут использоваться для загрузки значений. По умолчанию используется загрузчик `EnvLoader`, который загружает значения из переменных окружения. Вы можете добавить другие загрузчики, чтобы загружать значения из других источников.

Дескриптор принимает опциональные аргументы `default`, `default_factory` и `required`.

Если в классе конфигурации какое-либо поле помечено, дескриптором Load, но этого поля нет в конфигурационном yaml-файле, тогда будет проверяться значение аргумента `required`. Если значение `required` установлено в `True`, будет вызвано исключение `ValueError`. Иначе, будет использовано значение получаемое из `default_factory` или `default`. Функция, переданная в `default_factory`, будет вызвана без аргументов.

```python
# config.py
from dataclasses import dataclass
from dyacon import read_config, Load

@dataclass
class Config:
    token: str = Load(default_factory=lambda: "default_value")

config = read_config(Config)
```

### Загрузчики

Dyacon предоставляет несколько встроенных загрузчиков, которые могут быть использованы с дескриптором `Load`.

#### EnvLoader

Загрузчик `EnvLoader` загружает значения из переменных окружения. Для загрузки используется синтаксис `${env_variable_name:default_value}`. Если переменная окружения не установлена, будет использовано значение по умолчанию.

#### GoogleCloudSecretLoader

Загрузчик `GoogleCloudSecretLoader` загружает значения из Google Secret Manager. Для загрузки используется синтаксис `!{env_variable_name:project_id:default_value}`. Для работы с данным загрузчиком необходимо установить библиотеку `google-cloud-secret-manager` с помощью команды:

```shell
pip install "dyacon[google]"
```

или

```shell
pip install google-cloud-secret-manager
```

Так же необходимо установить переменную окружения `GOOGLE_APPLICATION_CREDENTIALS` с путем к файлу сервисного аккаунта Google Cloud.

Для использования загрузчика `GoogleCloudSecretLoader` необходимо передать его в список загрузчиков дескриптора `Load`. Так же вы можете реализовать свой дескриптор, просто унаследовавшись от `Load` и переопределив метод `__init__`.

```python
from typing import List, Optional, Callable, Any
from dyacon import Load, Loader
from dyacon.loaders.external import GoogleCloudSecretLoader

class NewLoad(Load):
    def __init__(
          self,
        loaders: Optional[List[Loader]] = None,
        *,
        default: Optional[str] = None,
        default_factory: Optional[Callable[[], Any]] = None,
        required: bool = False,
    ):
        super().__init__(
          loaders,
          default=default,
          default_factory=default_factory,
          required=required,
        )
        self.loaders.append(GoogleCloudSecretLoader())
```


## Вклад и обратная связь

Если у вас есть идеи, предложения или найдены баги, пожалуйста, поделитесь ими на [GitHub](https://github.com/morozov6420/dyacon). Ваш вклад приветствуется!

## Лицензия

Dyacon распространяется под лицензией MIT. Подробности см. в [LICENSE](LICENSE) файле.

---
Автор: [Aleksei Morozov](mailto:morozov6420@gmail.com) | [GitHub](https://github.com/morozov6420)
