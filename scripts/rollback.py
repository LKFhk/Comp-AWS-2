#!/usr/bin/env python3
"""
Rollback script for RiskIntel360 Platform
Rolls back to previous deployment version
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RollbackError(Exception):
    """Custom exception for rollback errors"""
    pass


class RiskIntel360Rollback:
    """Rollback manager for RiskIntel360 Platform"""
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Initialize AWS clients
        try:
            self.ecs_client = self.session.client('ecs')
            self.ssm_client = self.session.client('ssm')
            self.cloudformation_client = self.session.client('cloudformation')
            self.logs_client = self.session.client('logs')
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise RollbackError("AWS credentials not configured")
        
        # Environment-specific configuration
        self.stack_name = f"RiskIntel360Stack-{environment}"
        self.cluster_name = f"RiskIntel360-agents-{environment}"
        self.service_name = f"RiskIntel360-service-{environment}"
    
    async def rollback_deployment(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback deployment to previous version
        
        Args:
            target_version: Specific version to rollback to (optional)
            
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            logger.info(f"Starting rollback for {self.environment}")
            
            # Get deployment history
            deployment_history = await self._get_deployment_history()
            
            if not deployment_history:
                logger.error("No deployment history found")
                return False
            
            # Determine target version
            if target_version:
                target_deployment = await self._find_deployment_by_version(deployment_history, target_version)
            else:
                target_deployment = await self._get_previous_deployment(deployment_history)
            
            if not target_deployment:
                logger.error("No suitable deployment found for rollback")
                return False
            
            logger.info(f"Rolling back to version: {target_deployment['version']}")
            
            # Perform rollback
            success = await self._perform_rollback(target_deployment)
            
            if success:
                logger.info("Rollback completed successfully")
                await self._post_rollback_tasks(target_deployment)
            else:
                logger.error("Rollback failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            raise RollbackError(f"Rollback failed: {str(e)}")
    
    async def _get_deployment_history(self) -> List[Dict]:
        """Get deployment history from Parameter Store"""
        try:
            deployments = []
            
            # Get deployment history from Parameter Store
            paginator = self.ssm_client.get_paginator('get_parameters_by_path')
            
            for page in paginator.paginate(
                Path=f"/RiskIntel360/{self.environment}/deployments/",
                Recursive=True
            ):
                for parameter in page['Parameters']:
                    try:
                        deployment_data = json.loads(parameter['Value'])
                        deployment_data['parameter_name'] = parameter['Name']
                        deployments.append(deployment_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in parameter {parameter['Name']}")
            
            # Sort by deployment timestamp (newest first)
            deployments.sort(key=lambda x: x.get('deployed_at', ''), reverse=True)
            
            logger.info(f"Found {len(deployments)} deployments in history")
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to get deployment history: {str(e)}")
            return []
    
    async def _find_deployment_by_version(self, deployment_history: List[Dict], version: str) -> Optional[Dict]:
        """Find deployment by specific version"""
        for deployment in deployment_history:
            if deployment.get('version') == version or deployment.get('image_tag') == version:
                return deployment
        
        logger.error(f"Deployment version {version} not found in history")
        return None
    
    async def _get_previous_deployment(self, deployment_history: List[Dict]) -> Optional[Dict]:
        """Get the previous successful deployment"""
        if len(deployment_history) < 2:
            logger.error("Not enough deployment history for rollback")
            return None
        
        # Skip the current deployment (index 0) and get the previous one (index 1)
        return deployment_history[1]
    
    async def _perform_rollback(self, target_deployment: Dict) -> bool:
        """Perform the actual rollback"""
        try:
            # Get current service configuration
            current_service = await self._get_current_service()
            
            if not current_service:
                logger.error("Current service not found")
                return False
            
            # Create rollback task definition
            rollback_task_def_arn = await self._create_rollback_task_definition(target_deployment)
            
            if not rollback_task_def_arn:
                logger.error("Failed to create rollback task definition")
                return False
            
            # Update service with rollback task definition
            await self._update_service_for_rollback(rollback_task_def_arn)
            
            # Wait for rollback to complete
            success = await self._wait_for_rollback_completion()
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback execution failed: {str(e)}")
            return False
    
    async def _get_current_service(self) -> Optional[Dict]:
        """Get current ECS service configuration"""
        try:
            response = self.ecs_client.describe_services(
                cluster=self.cluster_name,
                services=[self.service_name]
            )
            
            if response['services']:
                return response['services'][0]
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get current service: {str(e)}")
            return None
    
    async def _create_rollback_task_definition(self, target_deployment: Dict) -> Optional[str]:
        """Create task definition for rollback"""
        try:
            # Get current task definition as template
            current_service = await self._get_current_service()
            
            if not current_service:
                return None
            
            current_task_def_arn = current_service['taskDefinition']
            
            response = self.ecs_client.describe_task_definition(
                taskDefinition=current_task_def_arn
            )
            
            current_task_def = response['taskDefinition']
            
            # Update container image to rollback version
            container_definitions = current_task_def['containerDefinitions']
            
            # Get ECR repository URI
            account_id = self.session.client('sts').get_caller_identity()['Account']
            rollback_image_tag = target_deployment.get('image_tag', target_deployment.get('version'))
            rollback_image_uri = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com/RiskIntel360-platform:{rollback_image_tag}"
            
            for container in container_definitions:
                if container['name'] == 'RiskIntel360-app':
                    container['image'] = rollback_image_uri
                    break
            
            # Register rollback task definition
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
                        'key': 'RollbackAt',
                        'value': datetime.utcnow().isoformat()
                    },
                    {
                        'key': 'RollbackToVersion',
                        'value': rollback_image_tag
                    }
                ]
            )
            
            rollback_task_def_arn = response['taskDefinition']['taskDefinitionArn']
            logger.info(f"Rollback task definition created: {rollback_task_def_arn}")
            
            return rollback_task_def_arn
            
        except Exception as e:
            logger.error(f"Failed to create rollback task definition: {str(e)}")
            return None
    
    async def _update_service_for_rollback(self, task_definition_arn: str) -> None:
        """Update ECS service for rollback"""
        try:
            logger.info("Updating service for rollback...")
            
            self.ecs_client.update_service(
                cluster=self.cluster_name,
                service=self.service_name,
                taskDefinition=task_definition_arn,
                forceNewDeployment=True
            )
            
            logger.info("Service rollback update initiated")
            
        except Exception as e:
            logger.error(f"Failed to update service for rollback: {str(e)}")
            raise
    
    async def _wait_for_rollback_completion(self, timeout: int = 1200) -> bool:
        """Wait for rollback to complete"""
        logger.info("Waiting for rollback to complete...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.ecs_client.describe_services(
                    cluster=self.cluster_name,
                    services=[self.service_name]
                )
                
                if not response['services']:
                    logger.error("Service not found during rollback")
                    return False
                
                service = response['services'][0]
                deployments = service['deployments']
                
                # Check if rollback deployment is stable
                primary_deployment = None
                for deployment in deployments:
                    if deployment['status'] == 'PRIMARY':
                        primary_deployment = deployment
                        break
                
                if primary_deployment:
                    if (primary_deployment['runningCount'] == primary_deployment['desiredCount'] and
                        primary_deployment['pendingCount'] == 0):
                        logger.info("Rollback completed successfully")
                        return True
                
                logger.info(f"Rollback in progress... Running: {primary_deployment['runningCount']}, "
                           f"Desired: {primary_deployment['desiredCount']}, "
                           f"Pending: {primary_deployment['pendingCount']}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error checking rollback status: {str(e)}")
                await asyncio.sleep(30)
        
        logger.error("Rollback timeout reached")
        return False
    
    async def _post_rollback_tasks(self, target_deployment: Dict) -> None:
        """Run post-rollback tasks"""
        logger.info("Running post-rollback tasks...")
        
        try:
            # Update current deployment metadata
            await self._update_current_deployment_metadata(target_deployment)
            
            # Log rollback event
            await self._log_rollback_event(target_deployment)
            
            # Send rollback notification
            await self._send_rollback_notification(target_deployment)
            
        except Exception as e:
            logger.warning(f"Post-rollback tasks failed: {str(e)}")
    
    async def _update_current_deployment_metadata(self, target_deployment: Dict) -> None:
        """Update current deployment metadata"""
        try:
            rollback_metadata = {
                'environment': self.environment,
                'version': target_deployment.get('version', target_deployment.get('image_tag')),
                'image_tag': target_deployment.get('image_tag'),
                'rolled_back_at': datetime.utcnow().isoformat(),
                'rolled_back_by': 'automated-rollback',
                'original_deployment': target_deployment
            }
            
            self.ssm_client.put_parameter(
                Name=f"/RiskIntel360/{self.environment}/deployment/current",
                Value=json.dumps(rollback_metadata),
                Type='String',
                Overwrite=True
            )
            
            # Also update the image tag parameter
            self.ssm_client.put_parameter(
                Name=f"/RiskIntel360/{self.environment}/image_tag",
                Value=target_deployment.get('image_tag', 'unknown'),
                Type='String',
                Overwrite=True
            )
            
        except Exception as e:
            logger.warning(f"Failed to update deployment metadata: {str(e)}")
    
    async def _log_rollback_event(self, target_deployment: Dict) -> None:
        """Log rollback event"""
        try:
            log_group = f"/aws/RiskIntel360/{self.environment}/application"
            
            rollback_event = {
                'event_type': 'rollback',
                'environment': self.environment,
                'target_version': target_deployment.get('version', target_deployment.get('image_tag')),
                'rollback_timestamp': datetime.utcnow().isoformat(),
                'rollback_reason': 'manual_rollback'
            }
            
            # Create log stream if it doesn't exist
            log_stream = f"rollback-{int(time.time())}"
            
            try:
                self.logs_client.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=log_stream
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Put log event
            self.logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=[
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': json.dumps(rollback_event)
                    }
                ]
            )
            
        except Exception as e:
            logger.warning(f"Failed to log rollback event: {str(e)}")
    
    async def _send_rollback_notification(self, target_deployment: Dict) -> None:
        """Send rollback notification"""
        try:
            # Placeholder for notification logic (Slack, SNS, etc.)
            version = target_deployment.get('version', target_deployment.get('image_tag'))
            logger.info(f"ROLLBACK NOTIFICATION: {self.environment} rolled back to version {version}")
            
        except Exception as e:
            logger.warning(f"Failed to send rollback notification: {str(e)}")
    
    async def list_deployment_history(self) -> None:
        """List deployment history"""
        try:
            deployment_history = await self._get_deployment_history()
            
            if not deployment_history:
                logger.info("No deployment history found")
                return
            
            logger.info(f"Deployment history for {self.environment}:")
            logger.info("-" * 80)
            
            for i, deployment in enumerate(deployment_history):
                status = "CURRENT" if i == 0 else f"PREVIOUS-{i}"
                version = deployment.get('version', deployment.get('image_tag', 'unknown'))
                deployed_at = deployment.get('deployed_at', 'unknown')
                deployed_by = deployment.get('deployed_by', 'unknown')
                
                logger.info(f"{status:12} | {version:20} | {deployed_at:20} | {deployed_by}")
            
        except Exception as e:
            logger.error(f"Failed to list deployment history: {str(e)}")


async def main():
    """Main rollback function"""
    parser = argparse.ArgumentParser(description='Rollback RiskIntel360 Platform deployment')
    parser.add_argument('--environment', required=True,
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--version', 
                       help='Specific version to rollback to (optional)')
    parser.add_argument('--list-history', action='store_true',
                       help='List deployment history')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    
    args = parser.parse_args()
    
    try:
        rollback_manager = RiskIntel360Rollback(args.environment, args.region)
        
        if args.list_history:
            await rollback_manager.list_deployment_history()
            sys.exit(0)
        
        success = await rollback_manager.rollback_deployment(args.version)
        
        if success:
            logger.info("Rollback completed successfully")
            sys.exit(0)
        else:
            logger.error("Rollback failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Rollback error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
