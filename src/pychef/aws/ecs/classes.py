import os
from dataclasses import dataclass, field
from typing import Dict, List

import boto3


@dataclass
class EcsTaskDefinitionConfig:
    """
    Represents a configuration for generating an AWS ECS task definition.

    Attributes:
        family (str): The ECS task family name .
        name (str): Container name.
        cpu (int): CPU units reserved for the container.
        memory_reservation (int): MemoryReservation (MiB) for the container.
        task_role_arn (str): IAM role ARN that the task assumes.
        execution_role_arn (str): IAM role ARN used by ECS agent for image pulls and log creation.
        network_mode (str): Docker networking mode (e.g., "bridge", "awsvpc").
        commands (List[str]): List of command-line arguments passed to the container.
        port_mappings (List[dict]): Container port mapping definitions.
        volumes (Dict[str, dict]): Mapping of container mount paths to ECS volume definitions.
        secrets (List[Dict[str, str]]): List of secret environment variable definitions.
        environments (List[Dict[str, str]]): List of environment variable definitions.
        awslog_region (str): AWS region for CloudWatch log, default to "AWS_DEFAULT_REGION" in environment variables.
        awslog_group (str): CloudWatch log group name.
        awslog_stream (str): CloudWatch log stream prefix, falls back to `family`.
    """
    family: str
    name: str = "app"
    cpu: int = 256
    memory_reservation: int = 512
    task_role_arn: str = ""
    execution_role_arn: str = ""
    network_mode: str = "bridge"
    commands: List[str] = field(default_factory=list)
    port_mappings: List[dict] = field(default_factory=list)
    volumes: Dict[str, dict] = field(default_factory=dict)
    secrets: List[Dict[str, str]] = field(default_factory=list)
    environments: List[Dict[str, str]] = field(default_factory=list)
    awslog_region: str = ""
    awslog_group: str = "default"
    awslog_stream: str = ""

    def __post_init__(self):
        if not self.awslog_stream:
            self.awslog_stream = self.family
        if not self.awslog_region:
            self.awslog_region = os.environ.get("AWS_DEFAULT_REGION", "")

    def generate_args(self, repo: str, tag: str) -> dict:
        """
            Builds and returns a complete ECS task definition arguments for register_task_definition(**kwargs).

            Args:
                repo (str): Docker image repository URI
                tag (str): Docker image tag

            Returns:
                dict: A ECS task definition arguments.
        """
        environments = self.environments + [
            {
                "name": "IMAGE_REPOSITORY",
                "value": repo,
            },
            {
                "name": "IMAGE_TAG",
                "value": tag,
            },
        ]
        return {
            "family": self.family,
            "volumes": [volume for volume in self.volumes.values()],
            "taskRoleArn": self.task_role_arn,
            "executionRoleArn": self.execution_role_arn,
            "networkMode": self.network_mode,
            "runtimePlatform": {"operatingSystemFamily": "LINUX"},
            "containerDefinitions": [
                {
                    "name": self.name,
                    # Only image URL are dynamic in each deployment
                    "image": f"{repo}:{tag}",
                    "essential": True,
                    "cpu": self.cpu,
                    "memoryReservation": self.memory_reservation,
                    "portMappings": self.port_mappings,
                    "command": self.commands,
                    "environment": environments,
                    "secrets": self.secrets,
                    "mountPoints": [
                        {
                            "containerPath": path,
                            "sourceVolume": volume["name"],
                        }
                        for path, volume in self.volumes.items()
                    ],
                    # Currently support CloudWatch Logs only
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-region": self.awslog_region,
                            "awslogs-group": self.awslog_group,
                            "awslogs-stream-prefix": self.awslog_stream,
                        },
                    },
                },
            ],
        }


@dataclass
class EcsServiceConfig:
    """
        Represents a partial configuration for generating an AWS ECS service.
    """
    name: str
    task_definition: EcsTaskDefinitionConfig

    def generate_args(self, cluster_name: str, task_arn: str) -> dict:
        """
            Builds and returns a complete ECS service arguments for update_service(**kwargs).

            Args:
                cluster_name (str): ECS cluster name
                task_arn (str): task definition ARN

            Returns:
                dict: A ECS service arguments.
        """
        return {
            "cluster": cluster_name,
            "service": self.name,
            "taskDefinition": task_arn,
        }


@dataclass
class EcsClusterConfig:
    """
        Represents a partial configuration of an AWS ECS cluster.

        Attributes:
        name (str): The name of the ECS cluster.
        services (List[EcsServiceConfig]): A list of ECS service configurations
            to be deployed within this cluster.
        runtask (Optional[EcsTaskDefinitionConfig]): Optional task definition
            configuration used for one-off ECS tasks (e.g., migrations, scripts).
    """
    name: str = "default"
    services: List[EcsServiceConfig] = field(default_factory=list)
    runtask: EcsTaskDefinitionConfig = None


class EcsDeployService:
    """A singleton class to deploy services or run one-off tasks on an ECS cluster."""
    def __init__(
        self,
        cluster: EcsClusterConfig,
        repo: str,
        tag: str,
        region: str = "",
    ):
        """Initialize the ECS deployment service.

        Args:
            cluster (EcsClusterConfig): The ECS cluster configuration.
            repo (str): The image repository.
            tag (str): The image tag to deploy.
            region (str): AWS region name for Secrets Manager, default to "AWS_DEFAULT_REGION" in environment variables.
        """
        self.repo = repo
        self.tag = tag
        self.cluster = cluster
        self.client = boto3.client(
            "ecs",
            region_name=region or os.environ.get("AWS_DEFAULT_REGION", "")
        )

    def update_task_definition(self, task_definition: EcsTaskDefinitionConfig) -> str:
        # 1. Check task definition exist or not
        task_definition_dict = task_definition.generate_args(self.repo, self.tag)
        self.client.describe_task_definition(taskDefinition=task_definition_dict["family"])
        # 2. Then update task definition
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/register_task_definition.html
        response = self.client.register_task_definition(**task_definition_dict)

        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Update ECS task Fail")
        task_definition_arn = response["taskDefinition"]["taskDefinitionArn"]
        return task_definition_arn

    def update_service(self, service: EcsServiceConfig, task_arn: str):
        update_service_args = service.generate_args(self.cluster.name, task_arn)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/update_service.html
        response = self.client.update_service(**update_service_args)
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Update ECS service fail")

    def create_deployment(self):
        """Deploys all ECS services defined in the cluster configuration."""
        for service in self.cluster.services:
            task_definition_arn = self.update_task_definition(service.task_definition)
            self.update_service(service, task_definition_arn)

    def create_runtask(self, commands: list[str] = None):
        """Runs an ECS one-off task with specified commands using `self.cluster.runtask` task definition.

        Args:
            commands (list[str]): Command list to override the container entrypoint.
            Will use predefined comamnd if not specified.

        Raises:
            RuntimeError: If the ECS API returns a non-200 response when running the task.
        """
        if self.cluster.runtask is None:
            return

        if type(commands) == list and len(commands) > 0:
            self.cluster.runtask.commands = commands
        task_definition_arn = self.update_task_definition(self.cluster.runtask)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/run_task.html
        response = self.client.run_task(
            cluster=self.cluster.name,
            taskDefinition=task_definition_arn,
            count=1,
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise RuntimeError("Describe ECS service Fail")
