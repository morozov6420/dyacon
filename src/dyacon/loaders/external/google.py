import importlib
import logging
import re
from typing import Optional, Pattern

from ..loaders import Loader

logger = logging.getLogger(__name__)


try:
    secretmanager = importlib.import_module('google.cloud.secretmanager')
    SecretManagerServiceClient = secretmanager.SecretManagerServiceClient
    exceptions = importlib.import_module('google.api_core.exceptions')
    NotFound = exceptions.NotFound
except ImportError:
    SecretManagerServiceClient = None
    NotFound = None


def get_google_cloud_secret(
    secret_id: str,
    google_project: str,
) -> Optional[str]:
    if SecretManagerServiceClient and NotFound:
        try:
            client = SecretManagerServiceClient()
            name = client.secret_version_path(
                google_project,
                secret_id,
                'latest',
            )
            response = client.access_secret_version(request={'name': name})
            secret = response.payload.data.decode('UTF-8')
            return secret
        except NotFound:
            logger.warning(
                f'Secret {secret_id} not found in project {google_project}'
            )
        return None
    logger.error(
        'google-cloud-secret-manager is not installed! '
        "Try to use 'pip install \"dyacon[google]\"' "
        "or 'pip install google-cloud-secret-manager' for installation"
    )
    return None


GOOGLE_CLOUD_SECRET_LOADER_PATTERN = re.compile(
    r'!{'
    r'(?P<name>[^}^{:]+)'
    r'(?P<first_separator>:?)'
    r'(?P<project_id>[^}^{:]+)'
    r'(?P<second_separator>:?)'
    r'(?P<default>.*?)'
    r'}',
)


class GoogleCloudSecretLoader(Loader):
    def __init__(self) -> None:
        self._pattern = GOOGLE_CLOUD_SECRET_LOADER_PATTERN

    @property
    def pattern(self) -> Pattern[str]:
        return self._pattern

    def load(self, config_content: str) -> str:
        findings = list(self.pattern.finditer(config_content))

        for match in reversed(findings):
            env_name = match.group('name')
            has_project_id = match.group('first_separator') == ':'
            has_default = match.group('second_separator') == ':'

            if not has_project_id:
                raise ValueError(
                    f'Project id is not specified for secret {env_name}'
                )
            project_id = match.group('project_id')

            value = get_google_cloud_secret(env_name, project_id)

            if value is None:
                if not has_default:
                    raise ValueError(
                        f'Missing required google cloud secret manager '
                        f'variable {env_name}'
                    )
                value = match.group('default')
            span_min, span_max = match.span()
            config_content = (
                f'{config_content[:span_min]}'
                f'{value}'
                f'{config_content[span_max:]}'
            )
        return config_content
