from unittest import TestCase

import boto3
import pytest
from moto import mock_aws
from moto.core import set_initial_no_auth_action_count

from pychef.aws.secrets_manager.classes import SecretManagerService


@mock_aws
class TestSecretManagerService(TestCase):
    def setUp(self):
        self.client = boto3.client("secretsmanager", region_name="ap-northeast-1")
        self.client.create_secret(Name="test/secret_a", SecretString="value_a")
        self.secrets_manager_service = SecretManagerService("test/")

    def test_fetch_secret_fail(self):
        with pytest.raises(RuntimeError) as exc:
            self.secrets_manager_service.fetch_secret("not_exist")
        assert "Failed to fetch secret with name test/not_exist" in str(exc)

    def test_fetch_secret_success(self):
        assert self.secrets_manager_service.fetch_secret("secret_a") == "value_a"

    def test_fetch_secrets_success(self):
        for i in range(20):
            self.client.create_secret(Name=f"test/secret_{i}", SecretString=f"value_{i}")
        result = self.secrets_manager_service.fetch_secrets()
        assert len(result) == 21  # With test/secret_a
        assert result["secret_a"] == "value_a"

    @set_initial_no_auth_action_count(0)
    def test_fetch_secrets_fail(self):
        with pytest.raises(RuntimeError) as exc:
            self.secrets_manager_service.fetch_secrets()
        assert "Failed to fetch secrets with prefix test/" in str(exc)
