"""
Audit Trail Logger for Compliance and Security
Logs all user actions and security events for audit trail compliance.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
import boto3
from botocore.exceptions import ClientError

from riskintel360.config.settings import get_settings
from .models import (
    AuditLogEntry, AuditAction, ResourceType, SecurityContext
)

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit trail logger for compliance and security monitoring"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cloudtrail_client = None
        self._cloudwatch_client = None
        self._dynamodb_client = None
        self._audit_table_name = None
        
        # Initialize AWS clients
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize AWS clients for audit logging"""
        try:
            # Initialize CloudWatch for custom metrics
            self._cloudwatch_client = boto3.client('cloudwatch')
            
            # Initialize DynamoDB for audit log storage
            self._dynamodb_client = boto3.client('dynamodb')
            self._audit_table_name = f"RiskIntel360-audit-logs-{self.settings.environment.value}"
            
            # Initialize CloudTrail client for API logging
            self._cloudtrail_client = boto3.client('cloudtrail')
            
            logger.info("Audit logger clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logger clients: {e}")
            # Continue without AWS clients for local development
    
    async def log_action(
        self,
        security_context: SecurityContext,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log user action for audit trail"""
        try:
            # Create audit log entry
            audit_entry = AuditLogEntry(
                id=str(uuid.uuid4()),
                user_id=security_context.user.id if security_context.user else "anonymous",
                tenant_id=security_context.tenant_id or "default",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=datetime.now(timezone.utc),
                ip_address=security_context.ip_address,
                user_agent=security_context.user_agent,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Log to application logger
            self._log_to_application_logger(audit_entry)
            
            # Store in DynamoDB
            await self._store_in_dynamodb(audit_entry)
            
            # Send CloudWatch metrics
            await self._send_cloudwatch_metrics(audit_entry)
            
            # Log to CloudTrail (for API actions)
            if action in [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]:
                await self._log_to_cloudtrail(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            # Don't raise exception to avoid breaking the main operation
    
    async def log_authentication(
        self,
        user_id: str,
        action: AuditAction,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log authentication events"""
        security_context = SecurityContext(
            user=None,  # User might not be available for failed logins
            tenant_id="default",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        await self.log_action(
            security_context=security_context,
            action=action,
            resource_type=ResourceType.USER_MANAGEMENT,
            resource_id=user_id,
            success=success,
            error_message=error_message,
            metadata={"event_type": "authentication"}
        )
    
    async def log_access_denied(
        self,
        security_context: SecurityContext,
        reason: str
    ) -> None:
        """Log access denied events"""
        await self.log_action(
            security_context=security_context,
            action=AuditAction.ACCESS_DENIED,
            resource_type=ResourceType.SYSTEM_CONFIG,
            success=False,
            error_message=reason,
            metadata={"event_type": "access_control"}
        )
    
    def _log_to_application_logger(self, audit_entry: AuditLogEntry) -> None:
        """Log audit entry to application logger"""
        log_data = {
            "audit_id": audit_entry.id,
            "user_id": audit_entry.user_id,
            "tenant_id": audit_entry.tenant_id,
            "action": audit_entry.action,
            "resource_type": audit_entry.resource_type,
            "resource_id": audit_entry.resource_id,
            "success": audit_entry.success,
            "timestamp": audit_entry.timestamp.isoformat(),
            "ip_address": audit_entry.ip_address,
        }
        
        if audit_entry.success:
            logger.info(f"AUDIT: {json.dumps(log_data)}")
        else:
            log_data["error"] = audit_entry.error_message
            logger.warning(f"AUDIT_FAILURE: {json.dumps(log_data)}")
    
    async def _store_in_dynamodb(self, audit_entry: AuditLogEntry) -> None:
        """Store audit entry in DynamoDB"""
        if not self._dynamodb_client or not self._audit_table_name:
            return
        
        try:
            # Prepare item for DynamoDB
            item = {
                'id': {'S': audit_entry.id},
                'user_id': {'S': audit_entry.user_id},
                'tenant_id': {'S': audit_entry.tenant_id},
                'action': {'S': audit_entry.action},
                'resource_type': {'S': audit_entry.resource_type},
                'timestamp': {'S': audit_entry.timestamp.isoformat()},
                'success': {'BOOL': audit_entry.success},
            }
            
            # Add optional fields
            if audit_entry.resource_id:
                item['resource_id'] = {'S': audit_entry.resource_id}
            
            if audit_entry.ip_address:
                item['ip_address'] = {'S': audit_entry.ip_address}
            
            if audit_entry.user_agent:
                item['user_agent'] = {'S': audit_entry.user_agent}
            
            if audit_entry.error_message:
                item['error_message'] = {'S': audit_entry.error_message}
            
            if audit_entry.metadata:
                item['metadata'] = {'S': json.dumps(audit_entry.metadata)}
            
            # Add TTL (30 days from now)
            ttl = int((datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60))
            item['ttl'] = {'N': str(ttl)}
            
            # Store in DynamoDB
            self._dynamodb_client.put_item(
                TableName=self._audit_table_name,
                Item=item
            )
            
        except ClientError as e:
            logger.error(f"Failed to store audit entry in DynamoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error storing audit entry: {e}")
    
    async def _send_cloudwatch_metrics(self, audit_entry: AuditLogEntry) -> None:
        """Send audit metrics to CloudWatch"""
        if not self._cloudwatch_client:
            return
        
        try:
            # Prepare metrics data
            metrics = [
                {
                    'MetricName': 'AuditEvents',
                    'Dimensions': [
                        {
                            'Name': 'Action',
                            'Value': audit_entry.action
                        },
                        {
                            'Name': 'ResourceType',
                            'Value': audit_entry.resource_type
                        },
                        {
                            'Name': 'Success',
                            'Value': str(audit_entry.success)
                        },
                        {
                            'Name': 'TenantId',
                            'Value': audit_entry.tenant_id
                        }
                    ],
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': audit_entry.timestamp
                }
            ]
            
            # Add failure-specific metrics
            if not audit_entry.success:
                metrics.append({
                    'MetricName': 'AuditFailures',
                    'Dimensions': [
                        {
                            'Name': 'Action',
                            'Value': audit_entry.action
                        },
                        {
                            'Name': 'ResourceType',
                            'Value': audit_entry.resource_type
                        }
                    ],
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': audit_entry.timestamp
                })
            
            # Send metrics to CloudWatch
            self._cloudwatch_client.put_metric_data(
                Namespace=self.settings.monitoring.cloudwatch_namespace,
                MetricData=metrics
            )
            
        except ClientError as e:
            logger.error(f"Failed to send CloudWatch metrics: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending metrics: {e}")
    
    async def _log_to_cloudtrail(self, audit_entry: AuditLogEntry) -> None:
        """Log API actions to CloudTrail"""
        if not self._cloudtrail_client:
            return
        
        try:
            # CloudTrail automatically logs API calls
            # This method can be used for custom events if needed
            logger.debug(f"CloudTrail logging for audit entry: {audit_entry.id}")
            
        except Exception as e:
            logger.error(f"CloudTrail logging error: {e}")
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[ResourceType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list[AuditLogEntry]:
        """Retrieve audit logs with filtering"""
        if not self._dynamodb_client or not self._audit_table_name:
            return []
        
        try:
            # Build query parameters
            scan_params = {
                'TableName': self._audit_table_name,
                'Limit': limit
            }
            
            # Add filters
            filter_expressions = []
            expression_values = {}
            
            if user_id:
                filter_expressions.append('user_id = :user_id')
                expression_values[':user_id'] = {'S': user_id}
            
            if tenant_id:
                filter_expressions.append('tenant_id = :tenant_id')
                expression_values[':tenant_id'] = {'S': tenant_id}
            
            if action:
                filter_expressions.append('#action = :action')
                expression_values[':action'] = {'S': action.value}
                scan_params['ExpressionAttributeNames'] = {'#action': 'action'}
            
            if resource_type:
                filter_expressions.append('resource_type = :resource_type')
                expression_values[':resource_type'] = {'S': resource_type.value}
            
            if start_time:
                filter_expressions.append('#timestamp >= :start_time')
                expression_values[':start_time'] = {'S': start_time.isoformat()}
                if 'ExpressionAttributeNames' not in scan_params:
                    scan_params['ExpressionAttributeNames'] = {}
                scan_params['ExpressionAttributeNames']['#timestamp'] = 'timestamp'
            
            if end_time:
                filter_expressions.append('#timestamp <= :end_time')
                expression_values[':end_time'] = {'S': end_time.isoformat()}
                if 'ExpressionAttributeNames' not in scan_params:
                    scan_params['ExpressionAttributeNames'] = {}
                scan_params['ExpressionAttributeNames']['#timestamp'] = 'timestamp'
            
            if filter_expressions:
                scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
                scan_params['ExpressionAttributeValues'] = expression_values
            
            # Execute scan
            response = self._dynamodb_client.scan(**scan_params)
            
            # Convert DynamoDB items to AuditLogEntry objects
            audit_logs = []
            for item in response.get('Items', []):
                try:
                    audit_log = self._dynamodb_item_to_audit_entry(item)
                    audit_logs.append(audit_log)
                except Exception as e:
                    logger.error(f"Failed to convert DynamoDB item to audit entry: {e}")
            
            return audit_logs
            
        except ClientError as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving audit logs: {e}")
            return []
    
    def _dynamodb_item_to_audit_entry(self, item: Dict[str, Any]) -> AuditLogEntry:
        """Convert DynamoDB item to AuditLogEntry"""
        return AuditLogEntry(
            id=item['id']['S'],
            user_id=item['user_id']['S'],
            tenant_id=item['tenant_id']['S'],
            action=item['action']['S'],
            resource_type=item['resource_type']['S'],
            resource_id=item.get('resource_id', {}).get('S'),
            timestamp=datetime.fromisoformat(item['timestamp']['S']),
            ip_address=item.get('ip_address', {}).get('S'),
            user_agent=item.get('user_agent', {}).get('S'),
            success=item['success']['BOOL'],
            error_message=item.get('error_message', {}).get('S'),
            metadata=json.loads(item.get('metadata', {}).get('S', '{}'))
        )
