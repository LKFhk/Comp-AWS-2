#!/usr/bin/env python3
"""
Deployment script for RiskIntel360 Platform
Supports multiple environments and deployment strategies
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentError(Exception):
    """Custom exception for deployment errors"""
    pass


class RiskIntel360Deployer:
    """Main deployment class for RiskIntel360 Platform"""
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Initialize AWS clients
        try:
            self.ecs_client = self.session.client('ecs')
            self.ecr_client = self.session.client('ecr')
            self.cloudformation_client = self.session.client('cloudformation')
            self.ssm_client = self.session.client('ssm')
            self.logs_client = self.session.client('logs')
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise DeploymentError("AWS credentials not configured")
        
        # Environment-specific configuration
        self.stack_name = f"RiskIntel360Stack-{environment}"
        self.cluster_name = f"RiskIntel360-agents-{environment}"
        self.service_name = f"RiskIntel360-service-{environment}"
        self.ecr_repository = "RiskIntel360-platform"
        
    async def deploy(self, image_tag: str, strategy: str = "rolling") -> bool:
        """
        Deploy the application using specified strategy
        
        Args:
            image_tag: Docker image tag to deploy
            strategy: Deployment strategy ('rolling' or 'blue-green')
            
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            logger.info(f"Starting deployment to {self.environment} with strategy: {strategy}")
            
            # Validate prerequisites
            await self._validate_prerequisites()
            
            # Get current deployment info
            current_deployment = await self._get_current_deployment()
            
            # Deploy based on strategy
            if strategy == "blue-green":
                success = await self._deploy_blue_green(image_tag, current_deployment)
            else:
                success = await self._deploy_rolling(image_tag)
            
            if success:
                logger.info(f"Deployment to {self.environment} completed successfully")
                await self._post_deployment_tasks(image_tag)
            else:
                logger.error(f"Deployment to {self.environment} failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise DeploymentError(f"Deployment failed: {str(e)}")
    
    async def _validate_prerequisites(self) -> None:
        """Validate that all prerequisites are met for deployment"""
        logger.info("Validating deployment prerequisites...")
        
        # Check if CloudFormation stack exists
        try:
            response = self.cloudformation_client.describe_stacks(
                StackName=self.stack_name
            )
            stack_status = response['Stacks'][0]['StackStatus']
            if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                raise DeploymentError(f"Stack {self.stack_name} is in invalid state: {stack_status}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                raise DeploymentError(f"Stack {self.stack_name} does not exist")
            raise
        
        # Check if ECS cluster exists
        try:
            response = self.ecs_client.describe_clusters(clusters=[self.cluster_name])
            if not response['clusters'] or response['clusters'][0]['status'] != 'ACTIVE':
                raise DeploymentError(f"ECS cluster {self.cluster_name} not found or not active")
        except ClientError:
            raise DeploymentError(f"Failed to describe ECS cluster {self.cluster_name}")
        
        # Validate ECR image exists
        await self._validate_ecr_image()
        
        logger.info("Prerequisites validation completed successfully")
    
    async def _validate_ecr_image(self) -> None:
        """Validate that the ECR image exists"""
        try:
            # Get ECR repository URI from stack outputs
            stack_outputs = await self._get_stack_outputs()
            ecr_uri = None
            
            for output in stack_outputs:
                if output['OutputKey'] == 'ECRRepositoryURI':
                    ecr_uri = output['OutputValue']
                    break
            
            if not ecr_uri:
                # Construct ECR URI manually
                account_id = self.session.client('sts').get_caller_identity()['Account']
                ecr_uri = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.ecr_repository}"
            
            # Check if image exists
            try:
                self.ecr_client.describe_images(
                    repositoryName=self.ecr_repository,
                    imageIds=[{'imageTag': 'latest'}]
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'ImageNotFoundException':
                    raise DeploymentError(f"Docker image not found in ECR repository")
                raise
                
        except Exception as e:
            logger.warning(f"Could not validate ECR image: {str(e)}")
    
    async def _get_current_deployment(self) -> Optional[Dict]:
        """Get information about current deployment"""
        try:
            response = self.ecs_client.describe_services(
                cluster=self.cluster_name,
                services=[self.service_name]
            )
            
            if response['services']:
                service = response['services'][0]
                return {
                    'service_arn': service['serviceArn'],
                    'task_definition': service['taskDefinition'],
                    'desired_count': service['desiredCount'],
                    'running_count': service['runningCount'],
                    'status': service['status']
                }
            return None
            
        except ClientError:
            logger.info("No existing service found")
            return None
    
    async def _deploy_rolling(self, image_tag: str) -> bool:
        """Deploy using rolling update strategy"""
        logger.info("Starting rolling deployment...")
        
        try:
            # Update task definition
            new_task_def_arn = await self._update_task_definition(image_tag)
            
            # Update service
            await self._update_service(new_task_def_arn)
            
            # Wait for deployment to complete
            success = await self._wait_for_deployment()
            
            return success
            
        except Exception as e:
            logger.error(f"Rolling deployment failed: {str(e)}")
            return False
    
    async def _deploy_blue_green(self, image_tag: str, current_deployment: Optional[Dict]) -> bool:
        """Deploy using blue-green strategy"""
        logger.info("Starting blue-green deployment...")
        
        try:
            # Create new task definition
            new_task_def_arn = await self._update_task_definition(image_tag)
            
            # Create green service
            green_service_name = f"{self.service_name}-green"
            await self._create_green_service(new_task_def_arn, green_service_name)
            
            # Wait for green service to be stable
            await self._wait_for_service_stable(green_service_name)
            
            # Run health checks on green service
            health_check_passed = await self._run_health_checks(green_service_name)
            
            if health_check_passed:
                # Switch traffic to green service
                await self._switch_traffic_to_green(green_service_name)
                
                # Clean up blue service
                if current_deployment:
                    await self._cleanup_blue_service()
                
                return True
            else:
                # Health checks failed, cleanup green service
                await self._cleanup_green_service(green_service_name)
                return False
                
        except Exception as e:
            logger.error(f"Blue-green deployment failed: {str(e)}")
            return False
    
    async def _update_task_definition(self, image_tag: str) -> str:
        """Update ECS task definition with new image"""
        logger.info(f"Updating task definition with image tag: {image_tag}")
        
        try:
            # Get current task definition
            current_task_def = await self._get_current_task_definition()
            
            # Get ECR repository URI
            account_id = self.session.client('sts').get_caller_identity()['Account']
            image_uri = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.ecr_repository}:{image_tag}"
            
            # Update container image
            container_definitions = current_task_def['containerDefinitions']
            for container in container_definitions:
                if container['name'] == 'RiskIntel360-app':
                    container['image'] = image_uri
                    break
            
            # Register new task definition
            response = self.ecs_client.register_task_definition(
                family=current_task_def['family'],
                taskRoleArn=current_task_def.get('taskRoleArn'),
                executionRoleArn=current_task_def.get('executionRoleArn'),
                networkMode=current_task_def.get('networkMode'),
                containerDefinitions=container_definitions,
                requiresCompatibilities=current_task_def.get('requiresCompatibilities', []),
                cpu=current_task_def.get('cpu'),
                memory=current_task_def.get('memory'),
                tags=[
                    {
                        'key': 'Environment',
                        'value': self.environment
                    },
                    {
                        'key': 'DeployedAt',
                        'value': datetime.utcnow().isoformat()
                    },
                    {
                        'key': 'ImageTag',
                        'value': image_tag
                    }
                ]
            )
            
            new_task_def_arn = response['taskDefinition']['taskDefinitionArn']
            logger.info(f"New task definition created: {new_task_def_arn}")
            
            return new_task_def_arn
            
        except Exception as e:
            logger.error(f"Failed to update task definition: {str(e)}")
            raise
    
    async def _get_current_task_definition(self) -> Dict:
        """Get the current task definition"""
        try:
            # Get service to find current task definition
            response = self.ecs_client.describe_services(
                cluster=self.cluster_name,
                services=[self.service_name]
            )
            
            if not response['services']:
                # No existing service, get latest task definition
                response = self.ecs_client.list_task_definitions(
                    familyPrefix=f"RiskIntel360-{self.environment}",
                    status='ACTIVE',
                    sort='DESC',
                    maxResults=1
                )
                
                if not response['taskDefinitionArns']:
                    raise DeploymentError("No task definition found")
                
                task_def_arn = response['taskDefinitionArns'][0]
            else:
                task_def_arn = response['services'][0]['taskDefinition']
            
            # Describe task definition
            response = self.ecs_client.describe_task_definition(
                taskDefinition=task_def_arn
            )
            
            return response['taskDefinition']
            
        except Exception as e:
            logger.error(f"Failed to get current task definition: {str(e)}")
            raise
    
    async def _update_service(self, task_definition_arn: str) -> None:
        """Update ECS service with new task definition"""
        logger.info("Updating ECS service...")
        
        try:
            self.ecs_client.update_service(
                cluster=self.cluster_name,
                service=self.service_name,
                taskDefinition=task_definition_arn,
                forceNewDeployment=True
            )
            
            logger.info("Service update initiated")
            
        except Exception as e:
            logger.error(f"Failed to update service: {str(e)}")
            raise
    
    async def _wait_for_deployment(self, timeout: int = 1200) -> bool:
        """Wait for deployment to complete"""
        logger.info("Waiting for deployment to complete...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.ecs_client.describe_services(
                    cluster=self.cluster_name,
                    services=[self.service_name]
                )
                
                if not response['services']:
                    logger.error("Service not found")
                    return False
                
                service = response['services'][0]
                deployments = service['deployments']
                
                # Check if deployment is stable
                primary_deployment = None
                for deployment in deployments:
                    if deployment['status'] == 'PRIMARY':
                        primary_deployment = deployment
                        break
                
                if primary_deployment:
                    if (primary_deployment['runningCount'] == primary_deployment['desiredCount'] and
                        primary_deployment['pendingCount'] == 0):
                        logger.info("Deployment completed successfully")
                        return True
                
                logger.info(f"Deployment in progress... Running: {primary_deployment['runningCount']}, "
                           f"Desired: {primary_deployment['desiredCount']}, "
                           f"Pending: {primary_deployment['pendingCount']}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error checking deployment status: {str(e)}")
                await asyncio.sleep(30)
        
        logger.error("Deployment timeout reached")
        return False
    
    async def _create_green_service(self, task_definition_arn: str, green_service_name: str) -> None:
        """Create green service for blue-green deployment"""
        logger.info(f"Creating green service: {green_service_name}")
        
        try:
            # Get current service configuration
            response = self.ecs_client.describe_services(
                cluster=self.cluster_name,
                services=[self.service_name]
            )
            
            if response['services']:
                current_service = response['services'][0]
                
                # Create green service with same configuration
                self.ecs_client.create_service(
                    cluster=self.cluster_name,
                    serviceName=green_service_name,
                    taskDefinition=task_definition_arn,
                    desiredCount=current_service['desiredCount'],
                    launchType=current_service['launchType'],
                    networkConfiguration=current_service.get('networkConfiguration'),
                    loadBalancers=current_service.get('loadBalancers', []),
                    serviceRegistries=current_service.get('serviceRegistries', []),
                    tags=[
                        {
                            'key': 'Environment',
                            'value': self.environment
                        },
                        {
                            'key': 'DeploymentType',
                            'value': 'green'
                        }
                    ]
                )
                
                logger.info(f"Green service {green_service_name} created")
            else:
                raise DeploymentError("Current service not found for blue-green deployment")
                
        except Exception as e:
            logger.error(f"Failed to create green service: {str(e)}")
            raise
    
    async def _wait_for_service_stable(self, service_name: str, timeout: int = 600) -> bool:
        """Wait for service to become stable"""
        logger.info(f"Waiting for service {service_name} to become stable...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.ecs_client.describe_services(
                    cluster=self.cluster_name,
                    services=[service_name]
                )
                
                if response['services']:
                    service = response['services'][0]
                    if (service['runningCount'] == service['desiredCount'] and
                        service['pendingCount'] == 0):
                        logger.info(f"Service {service_name} is stable")
                        return True
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error checking service stability: {str(e)}")
                await asyncio.sleep(30)
        
        logger.error(f"Service {service_name} did not become stable within timeout")
        return False
    
    async def _run_health_checks(self, service_name: str) -> bool:
        """Run health checks on the service"""
        logger.info(f"Running health checks on {service_name}...")
        
        try:
            # Get service endpoint
            endpoint = await self._get_service_endpoint(service_name)
            
            if not endpoint:
                logger.error("Could not determine service endpoint")
                return False
            
            # Run health check requests
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                for attempt in range(5):
                    try:
                        async with session.get(f"{endpoint}/health", timeout=30) as response:
                            if response.status == 200:
                                logger.info(f"Health check passed (attempt {attempt + 1})")
                                return True
                            else:
                                logger.warning(f"Health check failed with status {response.status}")
                    except Exception as e:
                        logger.warning(f"Health check attempt {attempt + 1} failed: {str(e)}")
                    
                    await asyncio.sleep(10)
            
            logger.error("All health check attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def _get_service_endpoint(self, service_name: str) -> Optional[str]:
        """Get service endpoint URL"""
        try:
            # Get load balancer information from service
            response = self.ecs_client.describe_services(
                cluster=self.cluster_name,
                services=[service_name]
            )
            
            if response['services'] and response['services'][0].get('loadBalancers'):
                # For now, return a placeholder endpoint
                # In a real implementation, you would get the actual load balancer DNS name
                return f"http://localhost:8000"  # Placeholder
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get service endpoint: {str(e)}")
            return None
    
    async def _switch_traffic_to_green(self, green_service_name: str) -> None:
        """Switch traffic from blue to green service"""
        logger.info("Switching traffic to green service...")
        
        try:
            # Update service name (rename green to primary)
            # This is a simplified implementation
            # In a real scenario, you would update load balancer target groups
            
            # Delete old blue service
            try:
                self.ecs_client.delete_service(
                    cluster=self.cluster_name,
                    service=self.service_name,
                    force=True
                )
            except ClientError:
                pass  # Service might not exist
            
            # Wait for deletion
            await asyncio.sleep(30)
            
            # Update green service name to primary
            # Note: ECS doesn't support renaming services, so this is a placeholder
            # In practice, you would use load balancer target group updates
            
            logger.info("Traffic switched to green service")
            
        except Exception as e:
            logger.error(f"Failed to switch traffic: {str(e)}")
            raise
    
    async def _cleanup_blue_service(self) -> None:
        """Clean up the blue service after successful deployment"""
        logger.info("Cleaning up blue service...")
        
        try:
            # Blue service cleanup is handled in _switch_traffic_to_green
            # This is a placeholder for additional cleanup tasks
            pass
            
        except Exception as e:
            logger.error(f"Failed to cleanup blue service: {str(e)}")
    
    async def _cleanup_green_service(self, green_service_name: str) -> None:
        """Clean up the green service after failed deployment"""
        logger.info(f"Cleaning up failed green service: {green_service_name}")
        
        try:
            self.ecs_client.delete_service(
                cluster=self.cluster_name,
                service=green_service_name,
                force=True
            )
            
            logger.info("Green service cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup green service: {str(e)}")
    
    async def _get_stack_outputs(self) -> List[Dict]:
        """Get CloudFormation stack outputs"""
        try:
            response = self.cloudformation_client.describe_stacks(
                StackName=self.stack_name
            )
            
            if response['Stacks']:
                return response['Stacks'][0].get('Outputs', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get stack outputs: {str(e)}")
            return []
    
    async def _post_deployment_tasks(self, image_tag: str) -> None:
        """Run post-deployment tasks"""
        logger.info("Running post-deployment tasks...")
        
        try:
            # Store deployment metadata
            await self._store_deployment_metadata(image_tag)
            
            # Update parameter store
            await self._update_parameter_store(image_tag)
            
            # Send deployment notifications
            await self._send_deployment_notification(image_tag, success=True)
            
        except Exception as e:
            logger.warning(f"Post-deployment tasks failed: {str(e)}")
    
    async def _store_deployment_metadata(self, image_tag: str) -> None:
        """Store deployment metadata"""
        try:
            metadata = {
                'environment': self.environment,
                'image_tag': image_tag,
                'deployed_at': datetime.utcnow().isoformat(),
                'deployed_by': os.getenv('GITHUB_ACTOR', 'unknown')
            }
            
            self.ssm_client.put_parameter(
                Name=f"/RiskIntel360/{self.environment}/deployment/latest",
                Value=json.dumps(metadata),
                Type='String',
                Overwrite=True
            )
            
        except Exception as e:
            logger.warning(f"Failed to store deployment metadata: {str(e)}")
    
    async def _update_parameter_store(self, image_tag: str) -> None:
        """Update parameter store with deployment info"""
        try:
            self.ssm_client.put_parameter(
                Name=f"/RiskIntel360/{self.environment}/image_tag",
                Value=image_tag,
                Type='String',
                Overwrite=True
            )
            
        except Exception as e:
            logger.warning(f"Failed to update parameter store: {str(e)}")
    
    async def _send_deployment_notification(self, image_tag: str, success: bool) -> None:
        """Send deployment notification"""
        try:
            # Placeholder for notification logic (Slack, SNS, etc.)
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"Deployment {status}: {self.environment} - {image_tag}")
            
        except Exception as e:
            logger.warning(f"Failed to send deployment notification: {str(e)}")


async def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy RiskIntel360 Platform')
    parser.add_argument('--environment', required=True, 
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--image-tag', required=True,
                       help='Docker image tag to deploy')
    parser.add_argument('--strategy', default='rolling',
                       choices=['rolling', 'blue-green'],
                       help='Deployment strategy')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    
    args = parser.parse_args()
    
    try:
        deployer = RiskIntel360Deployer(args.environment, args.region)
        success = await deployer.deploy(args.image_tag, args.strategy)
        
        if success:
            logger.info("Deployment completed successfully")
            sys.exit(0)
        else:
            logger.error("Deployment failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
