import os
from collections import defaultdict

import boto3


class SecretManagerService:
    """
        A singleton class to retrieve values from Secrets Manager.
    """
    def __init__(self, prefix: str = "", region: str = ""):
        """
        Args:
            prefix (str): A string prefix used to filter secrets by name if given.
            region (str): AWS region name for Secrets Manager, default to "AWS_DEFAULT_REGION" in environment variables.
        """
        self.prefix = prefix
        self.client = boto3.client(
            "secretsmanager",
            region_name=region or os.environ.get("AWS_DEFAULT_REGION", "")
        )

    def fetch_secrets(self) -> dict[str]:
        """
        Fetch all secrets from AWS Secrets Manager that match the prefix.

        Returns:
            dict[str, str]: A dictionary of secret names (without prefix) to secret values.

        Raises:
            RuntimeError: If the secrets cannot be fetched due to any exception.
        """
        prefix_length = len(self.prefix)
        result = defaultdict(str)
        args = {
            "Filters": [
                {
                    "Key": "name",
                    "Values": [self.prefix]
                }
            ],
            "MaxResults": 20,
        }
        try:
            response: dict = self.client.batch_get_secret_value(**args)
            for secret in response["SecretValues"]:
                result[secret["Name"][prefix_length:]] = secret["SecretString"]

            while response.get("NextToken"):
                args["NextToken"] = response.get("NextToken")
                response: dict = self.client.batch_get_secret_value(**args)
                for secret in response["SecretValues"]:
                    result[secret["Name"][prefix_length:]] = secret["SecretString"]
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to fetch secrets with prefix {self.prefix}") from e

    def fetch_secret(self, key: str) -> str:
        """
        Fetch a secret from AWS Secrets Manager using the combined name of the prefix and key.

        Args:
            key (str): The name of the secret without the prefix.

        Returns:
            str: The secret value as a string.

        Raises:
            RuntimeError: If the secret cannot be fetched due to any exception.
        """
        try:
            return self.client.get_secret_value(SecretId=f"{self.prefix}{key}")["SecretString"]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch secret with name {self.prefix}{key}") from e
