Russian version: [README.ru.md](README.ru.md)

# Dyacon

Dyacon is a library for working with YAML configurations in Python. It provides tools for convenient configuration loading and processing and supports loading values from environment variables and other sources, such as Google Secret Manager.

Using multiple configuration files allows you to store multiple sets of settings for one service simultaneously, making it easy to switch between them for different purposes, such as testing or debugging.

## Installation

You can install `dyacon` using pip:

```shell
pip install dyacon
```

If you want to use Google Secret Manager support, install the library with the appropriate options and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your Google Cloud service account file:

```shell
pip install "dyacon[google]"
```

## Why Use Dyacon?

The Dyacon library is designed to simplify working with YAML configurations in your Python applications. It offers the following features:

- **Combining Multiple YAML Files into One**: Dyacon allows you to create a hierarchy of configurations by collecting data from multiple files. This is convenient for splitting configuration into different files and components. For more details, read the [Loading Configuration](#loading-configuration) section.

- **Loading Values from Environment Variables**: Dyacon allows you to include values from environment variables in your configuration. You can use the special syntax `${env_variable_name:default_value}` to specify the name of the environment variable to look for and a default value.
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

- **Loading Values from Google Secret Manager**: If you work in the Google Cloud, Dyacon provides a loader for Google Secret Manager. You can load confidential data such as passwords and keys from Secret Manager using the syntax `${env_variable_name:project_id:default_value}`.
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

## Usage

### Loading Configuration

Dyacon provides tools for loading configuration from a YAML file and converting it into Python objects. A target configuration file must be created in which other files will be included, if necessary. For example, in the example below, the file `config/config.yaml` includes the file `db/local.yaml`. If you want to use settings for a production environment, you can create a file with a different name, such as `db/prod.yaml`, and include it in `config/config.yaml` using the `!include db/prod.yaml` directive. The path in the `!include` directive should be relative to the file in which it is used.

As a result, we would only need to change one line in the configuration file to switch to different settings.

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

The `read_config` function takes an optional `path` argument that specifies the target YAML file to load. If the argument is not provided, Dyacon will look for the `config/config.yaml` file relative to the current working directory.

### Load Descriptor

The `Load` descriptor allows you to inject automatic configuration value loading from various sources. `Load` takes a list of loaders that will be used to load values. By default, the `EnvLoader` loader is used, which loads values from environment variables. You can add other loaders to load values from other sources.

The descriptor accepts optional arguments `default`, `default_factory`, and `required`.

If a field in the configuration class is marked with the `Load` descriptor, but that field is not present in the configuration YAML file, the `required` argument will be checked. If the `required` value is set to `True`, a `ValueError` exception will be raised. Otherwise, the value obtained from `default_factory` or `default` will be used. The function provided in `default_factory` will be called without arguments.

```python
# config.py
from dataclasses import dataclass
from dyacon import read_config, Load

@dataclass
class Config:
    token: str = Load(default_factory=lambda: "default_value")

config = read_config(Config)
```

### Loaders

Dyacon provides several built-in loaders that can be used with the `Load` descriptor.

#### EnvLoader

The `EnvLoader` loader loads values from environment variables. To load values, use the `${env_variable_name:default_value}` syntax. If the environment variable is not set, the default value will be used.

#### GoogleCloudSecretLoader

The `GoogleCloudSecretLoader` loader loads values from Google Secret Manager. To load values, use the `!{env_variable_name:project_id:default_value}` syntax. To use this loader, you need to install the `google-cloud-secret-manager` library with the following command:

```shell
pip install "dyacon[google]"
```

or

```shell
pip install google-cloud-secret-manager
```

You also need to set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your Google Cloud service account file.

To use the `GoogleCloudSecretLoader` loader, pass it in the list of loaders for the `Load` descriptor. You can also implement your own descriptor by inheriting from `Load` and overriding the `__init__` method.

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

## Contributions and Feedback

If you have ideas, suggestions, or find bugs, please share them on [GitHub](https://github.com/morozov6420/dyacon). Your contributions are welcome!

## License

Dyacon is distributed under the MIT license. See the [LICENSE](LICENSE) file for details.

---
Author: [Aleksei Morozov](mailto:morozov6420@gmail.com) | [GitHub](https://github.com/morozov6420)
