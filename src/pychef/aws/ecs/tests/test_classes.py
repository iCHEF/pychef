from unittest import TestCase

import boto3
import pytest
from moto import mock_aws

from pychef.aws.ecs.classes import (EcsClusterConfig, EcsDeployService,
                                    EcsServiceConfig, EcsTaskDefinitionConfig)


@mock_aws
class TestEcsDeployService(TestCase):
    def setUp(self):
        # Create mock ECS client
        self.client = boto3.client("ecs", region_name="ap-northeast-1")
        self.client.create_cluster(clusterName="test-cluster")
        # Create a dummy service manually so ECS has it
        self.client.create_service(
            cluster="test-cluster",
            serviceName="test-service",
            desiredCount=1,
            taskDefinition=self.client.register_task_definition(
                family="test-family",
                containerDefinitions=[
                    {
                        "name": "app",
                        "image": "repo/url:v0",
                        "cpu": 100,
                        "memory": 200,
                    }
                ],
            )["taskDefinition"]["taskDefinitionArn"]
        )
        # Prepare configs
        self.ecs_task_definition = EcsTaskDefinitionConfig(
            family="test-family",
            awslog_region="ap-northeast-1",
            awslog_group="test-log-group",
            awslog_stream="test-log-stream",
        )
        self.ecs_service = EcsServiceConfig(name="test-service", task_definition=self.ecs_task_definition)
        self.ecs_cluster = EcsClusterConfig(
            name="test-cluster",
            services=[self.ecs_service],
            runtask=self.ecs_task_definition
        )
        self.deploy_service = EcsDeployService(cluster=self.ecs_cluster, repo="repo/url", tag="v1")

    def test_task_definition_post_init(self):
        assert EcsTaskDefinitionConfig(
            family="test-family",
        ).generate_args("repo/url", "v1")["containerDefinitions"][0]["logConfiguration"]["options"] == {
            "awslogs-group": "default",
            "awslogs-region": "ap-northeast-1",
            "awslogs-stream-prefix": "test-family",
        }

    def test_task_definition_generate_args(self):
        assert self.ecs_task_definition.generate_args("repo/url", "v1") == {
            "containerDefinitions": [
                {
                    "command": [],
                    "cpu": 256,
                    "environment": [
                        {
                            "name": "IMAGE_REPOSITORY",
                            "value": "repo/url",
                        },
                        {
                            "name": "IMAGE_TAG",
                            "value": "v1",
                        },
                    ],
                    "essential": True,
                    "image": "repo/url:v1",
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "test-log-group",
                            "awslogs-region": "ap-northeast-1",
                            "awslogs-stream-prefix": "test-log-stream",
                        },
                    },
                    "memoryReservation": 512,
                    "mountPoints": [],
                    "name": "app",
                    "portMappings": [],
                    "secrets": [],
                },
            ],
            "executionRoleArn": "",
            "family": "test-family",
            "networkMode": "bridge",
            "runtimePlatform": {
                "operatingSystemFamily": "LINUX",
            },
            "taskRoleArn": "",
            "volumes": [],
        }

    def test_update_task_definition_success(self):
        self.deploy_service.update_task_definition(
            self.deploy_service.cluster.services[0].task_definition
        )
        response = self.client.describe_task_definition(taskDefinition="test-family")
        assert response["taskDefinition"]["containerDefinitions"][0]["image"] == "repo/url:v1"

    def test_update_service_success(self):
        """Should create and update ECS service successfully"""
        arn = self.deploy_service.update_task_definition(self.ecs_task_definition)
        self.deploy_service.update_service(self.ecs_cluster.services[0], arn)

        resp = self.client.describe_services(cluster="test-cluster", services=["test-service"])
        assert resp["services"][0]["taskDefinition"] == arn

    def test_create_deployment(self):
        self.deploy_service.create_deployment()
        self.client.describe_services(cluster="test-cluster", services=["test-service"])

    def test_create_runtask_success(self):
        ec2_client = boto3.client("ec2")
        instance_id = ec2_client.run_instances(
            ImageId="ami-1234567",
            MinCount=1,
            MaxCount=1,
        )["Instances"][0]["InstanceId"]
        self.client.register_container_instance(
            cluster="test-cluster",
            instanceIdentityDocument='{{"instanceId": "{}"}}'.format(instance_id)
        )
        self.deploy_service.create_runtask(["echo", "'hello'", "'world'"])

    def test_create_runtask_fail(self):
        with pytest.raises(Exception, match="No instances found in cluster test-cluster"):
            self.deploy_service.create_runtask(["echo", "'hello'", "'world'"])

    def test_create_runtask_empty(self):
        self.ecs_cluster.runtask = None
        self.deploy_service.create_runtask(["echo", "'hello'", "'world'"])
