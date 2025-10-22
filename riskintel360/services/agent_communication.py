"""
Agent Communication Protocols with AgentCore Integration
Implements asyncio-based message routing and inter-agent communication.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
import json
import uuid

from .agentcore_client import AgentCoreClient, AgentCorePrimitive
from ..models.agent_models import (
    AgentMessage, MessageType, Priority, AgentType,
    AgentState, SessionStatus
)

logger = logging.getLogger(__name__)


class CommunicationProtocol(Enum):
    """Communication protocol types"""
    DIRECT_MESSAGE = "direct_message"
    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    REQUEST_RESPONSE = "request_response"
    PUBLISH_SUBSCRIBE = "publish_subscribe"


class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class MessageRoute:
    """Message routing information"""
    sender_id: str
    recipient_id: str
    protocol: CommunicationProtocol
    priority: Priority
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class MessageDeliveryReceipt:
    """Message delivery receipt"""
    message_id: str
    status: MessageStatus
    delivered_at: datetime
    acknowledged_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AgentCommunicationManager:
    """
    Manages agent communication protocols using asyncio queues and AgentCore coordination.
    Provides message routing, delivery guarantees, and inter-agent coordination.
    """
    
    def __init__(self, agentcore_client: AgentCoreClient, cleanup_interval: int = 60, message_process_interval: float = 0.1):
        """
        Initialize communication manager with AgentCore client.
        
        Args:
            agentcore_client: AgentCore client for message routing
            cleanup_interval: Interval in seconds for cleanup task (default: 60)
            message_process_interval: Interval in seconds for message processing (default: 0.1)
        """
        self.agentcore_client = agentcore_client
        self.cleanup_interval = cleanup_interval
        self.message_process_interval = message_process_interval
        
        # Message queues for each agent
        self.agent_queues: Dict[str, asyncio.Queue] = {}
        
        # Message handlers for each agent
        self.message_handlers: Dict[str, Callable] = {}
        
        # Active subscriptions for publish-subscribe
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of agent_ids
        
        # Message routing table
        self.routing_table: Dict[str, MessageRoute] = {}
        
        # Delivery receipts
        self.delivery_receipts: Dict[str, MessageDeliveryReceipt] = {}
        
        # Communication statistics
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "active_agents": 0
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._message_processor_task: Optional[asyncio.Task] = None
        
        logger.info("??AgentCommunicationManager initialized")
    
    async def start(self) -> None:
        """Start the communication manager background tasks"""
        try:
            # Start message cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
            
            # Start message processor task
            self._message_processor_task = asyncio.create_task(self._process_message_queue())
            
            logger.info("??Communication manager started")
            
        except Exception as e:
            logger.error(f"??Failed to start communication manager: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the communication manager and cleanup resources"""
        try:
            # Cancel background tasks and wait for them to complete
            tasks_to_cancel = []
            
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                tasks_to_cancel.append(self._cleanup_task)
            
            if self._message_processor_task and not self._message_processor_task.done():
                self._message_processor_task.cancel()
                tasks_to_cancel.append(self._message_processor_task)
            
            # Wait for all tasks to be cancelled
            if tasks_to_cancel:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            
            # Clear queues
            for queue in self.agent_queues.values():
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
            
            logger.info("??Communication manager stopped")
            
        except Exception as e:
            logger.error(f"??Error stopping communication manager: {e}")
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        message_handler: Optional[Callable] = None
    ) -> bool:
        """
        Register an agent for communication.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            message_handler: Optional message handler function
            
        Returns:
            bool: True if registration successful
        """
        try:
            # Create message queue for agent
            self.agent_queues[agent_id] = asyncio.Queue(maxsize=100)
            
            # Register message handler
            if message_handler:
                self.message_handlers[agent_id] = message_handler
            else:
                # Default message handler
                self.message_handlers[agent_id] = self._default_message_handler
            
            # Register with AgentCore
            success = self.agentcore_client.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=["messaging", "communication"],
                message_handler=self.message_handlers[agent_id]
            )
            
            if success:
                self.stats["active_agents"] += 1
                logger.info(f"??Agent {agent_id} registered for communication")
                return True
            else:
                # Cleanup on failure
                if agent_id in self.agent_queues:
                    del self.agent_queues[agent_id]
                if agent_id in self.message_handlers:
                    del self.message_handlers[agent_id]
                return False
            
        except Exception as e:
            logger.error(f"??Failed to register agent {agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from communication.
        
        Args:
            agent_id: Agent identifier to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            # Unregister from AgentCore
            success = self.agentcore_client.unregister_agent(agent_id)
            
            # Cleanup local resources
            if agent_id in self.agent_queues:
                del self.agent_queues[agent_id]
            
            if agent_id in self.message_handlers:
                del self.message_handlers[agent_id]
            
            # Remove from subscriptions
            for topic, subscribers in self.subscriptions.items():
                subscribers.discard(agent_id)
            
            if success:
                self.stats["active_agents"] = max(0, self.stats["active_agents"] - 1)
                logger.info(f"??Agent {agent_id} unregistered from communication")
            
            return success
            
        except Exception as e:
            logger.error(f"??Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        protocol: CommunicationProtocol = CommunicationProtocol.DIRECT_MESSAGE,
        expires_in: Optional[timedelta] = None
    ) -> str:
        """
        Send a message between agents using specified protocol.
        
        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID
            message_type: Type of message
            content: Message content
            priority: Message priority
            protocol: Communication protocol to use
            expires_in: Optional message expiration time
            
        Returns:
            str: Message ID
        """
        try:
            # Create message
            message = AgentMessage(
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
                priority=priority,
                expires_at=datetime.now(UTC) + expires_in if expires_in else None
            )
            
            # Create routing information
            route = MessageRoute(
                sender_id=sender_id,
                recipient_id=recipient_id,
                protocol=protocol,
                priority=priority,
                created_at=datetime.now(UTC),
                expires_at=message.expires_at
            )
            
            self.routing_table[message.message_id] = route
            
            # Route message based on protocol
            success = await self._route_message(message, protocol)
            
            if success:
                self.stats["messages_sent"] += 1
                logger.info(f"??Message {message.message_id} sent from {sender_id} to {recipient_id}")
            else:
                self.stats["messages_failed"] += 1
                logger.error(f"??Failed to send message {message.message_id}")
            
            return message.message_id
            
        except Exception as e:
            logger.error(f"??Error sending message: {e}")
            self.stats["messages_failed"] += 1
            raise
    
    async def _route_message(
        self,
        message: AgentMessage,
        protocol: CommunicationProtocol
    ) -> bool:
        """
        Route message using specified protocol.
        
        Args:
            message: Message to route
            protocol: Communication protocol
            
        Returns:
            bool: True if routing successful
        """
        try:
            if protocol == CommunicationProtocol.DIRECT_MESSAGE:
                return await self._route_direct_message(message)
            elif protocol == CommunicationProtocol.BROADCAST:
                return await self._route_broadcast_message(message)
            elif protocol == CommunicationProtocol.MULTICAST:
                return await self._route_multicast_message(message)
            elif protocol == CommunicationProtocol.REQUEST_RESPONSE:
                return await self._route_request_response_message(message)
            elif protocol == CommunicationProtocol.PUBLISH_SUBSCRIBE:
                return await self._route_publish_subscribe_message(message)
            else:
                logger.error(f"??Unknown protocol: {protocol}")
                return False
                
        except Exception as e:
            logger.error(f"??Message routing failed: {e}")
            return False
    
    async def _route_direct_message(self, message: AgentMessage) -> bool:
        """Route direct message to specific recipient"""
        try:
            # Deliver to local queue if recipient is registered
            if message.recipient_id in self.agent_queues:
                await self.agent_queues[message.recipient_id].put(message)
                
                # Create delivery receipt
                self.delivery_receipts[message.message_id] = MessageDeliveryReceipt(
                    message_id=message.message_id,
                    status=MessageStatus.DELIVERED,
                    delivered_at=datetime.now(UTC)
                )
                
                self.stats["messages_delivered"] += 1
                
                # Also notify AgentCore (but don't fail if it doesn't work)
                try:
                    response = await self.agentcore_client.route_message(
                        sender_id=message.sender_id,
                        recipient_id=message.recipient_id,
                        message=message
                    )
                    logger.debug(f"??AgentCore routing {'succeeded' if response.success else 'failed'} for message {message.message_id}")
                except Exception as e:
                    logger.debug(f"? ï? AgentCore routing failed for message {message.message_id}: {e}")
                
                return True
            else:
                logger.warning(f"??Recipient {message.recipient_id} not registered")
                return False
            
        except Exception as e:
            logger.error(f"??Direct message routing failed: {e}")
            return False
    
    async def _route_broadcast_message(self, message: AgentMessage) -> bool:
        """Route broadcast message to all registered agents"""
        try:
            success_count = 0
            
            for agent_id in self.agent_queues.keys():
                if agent_id != message.sender_id:  # Don't send to sender
                    # Create copy of message for each recipient
                    broadcast_message = AgentMessage(
                        sender_id=message.sender_id,
                        recipient_id=agent_id,
                        message_type=message.message_type,
                        content=message.content,
                        priority=message.priority,
                        correlation_id=message.correlation_id,
                        expires_at=message.expires_at
                    )
                    
                    # Deliver to local queue
                    await self.agent_queues[agent_id].put(broadcast_message)
                    success_count += 1
                    
                    # Also notify AgentCore (but don't fail if it doesn't work)
                    try:
                        response = await self.agentcore_client.route_message(
                            sender_id=message.sender_id,
                            recipient_id=agent_id,
                            message=broadcast_message
                        )
                        logger.debug(f"??AgentCore broadcast routing {'succeeded' if response.success else 'failed'} for {agent_id}")
                    except Exception as e:
                        logger.debug(f"? ï? AgentCore broadcast routing failed for {agent_id}: {e}")
            
            # Consider broadcast successful if at least one delivery succeeded
            if success_count > 0:
                self.delivery_receipts[message.message_id] = MessageDeliveryReceipt(
                    message_id=message.message_id,
                    status=MessageStatus.DELIVERED,
                    delivered_at=datetime.now(UTC)
                )
                self.stats["messages_delivered"] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"??Broadcast message routing failed: {e}")
            return False
    
    async def _route_multicast_message(self, message: AgentMessage) -> bool:
        """Route multicast message to specified group of recipients"""
        try:
            # Extract recipient list from message content
            recipients = message.content.get("recipients", [])
            success_count = 0
            
            for recipient_id in recipients:
                if recipient_id in self.agent_queues:
                    multicast_message = AgentMessage(
                        sender_id=message.sender_id,
                        recipient_id=recipient_id,
                        message_type=message.message_type,
                        content=message.content,
                        priority=message.priority,
                        correlation_id=message.correlation_id,
                        expires_at=message.expires_at
                    )
                    
                    response = await self.agentcore_client.route_message(
                        sender_id=message.sender_id,
                        recipient_id=recipient_id,
                        message=multicast_message
                    )
                    
                    if response.success:
                        await self.agent_queues[recipient_id].put(multicast_message)
                        success_count += 1
            
            if success_count > 0:
                self.delivery_receipts[message.message_id] = MessageDeliveryReceipt(
                    message_id=message.message_id,
                    status=MessageStatus.DELIVERED,
                    delivered_at=datetime.now(UTC)
                )
                self.stats["messages_delivered"] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"??Multicast message routing failed: {e}")
            return False
    
    async def _route_request_response_message(self, message: AgentMessage) -> bool:
        """Route request-response message with correlation tracking"""
        try:
            # Set correlation ID for response tracking
            if not message.correlation_id:
                message.correlation_id = str(uuid.uuid4())
            
            # Route as direct message
            return await self._route_direct_message(message)
            
        except Exception as e:
            logger.error(f"??Request-response message routing failed: {e}")
            return False
    
    async def _route_publish_subscribe_message(self, message: AgentMessage) -> bool:
        """Route publish-subscribe message to topic subscribers"""
        try:
            topic = message.content.get("topic")
            if not topic:
                logger.error("??Publish-subscribe message missing topic")
                return False
            
            subscribers = self.subscriptions.get(topic, set())
            success_count = 0
            
            for subscriber_id in subscribers:
                if subscriber_id in self.agent_queues:
                    pub_sub_message = AgentMessage(
                        sender_id=message.sender_id,
                        recipient_id=subscriber_id,
                        message_type=message.message_type,
                        content=message.content,
                        priority=message.priority,
                        correlation_id=message.correlation_id,
                        expires_at=message.expires_at
                    )
                    
                    response = await self.agentcore_client.route_message(
                        sender_id=message.sender_id,
                        recipient_id=subscriber_id,
                        message=pub_sub_message
                    )
                    
                    if response.success:
                        await self.agent_queues[subscriber_id].put(pub_sub_message)
                        success_count += 1
            
            if success_count > 0:
                self.delivery_receipts[message.message_id] = MessageDeliveryReceipt(
                    message_id=message.message_id,
                    status=MessageStatus.DELIVERED,
                    delivered_at=datetime.now(UTC)
                )
                self.stats["messages_delivered"] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"??Publish-subscribe message routing failed: {e}")
            return False
    
    async def subscribe_to_topic(self, agent_id: str, topic: str) -> bool:
        """
        Subscribe an agent to a topic for publish-subscribe messaging.
        
        Args:
            agent_id: Agent identifier
            topic: Topic to subscribe to
            
        Returns:
            bool: True if subscription successful
        """
        try:
            if agent_id not in self.agent_queues:
                logger.error(f"??Agent {agent_id} not registered")
                return False
            
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            
            self.subscriptions[topic].add(agent_id)
            logger.info(f"??Agent {agent_id} subscribed to topic '{topic}'")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to subscribe agent {agent_id} to topic '{topic}': {e}")
            return False
    
    async def unsubscribe_from_topic(self, agent_id: str, topic: str) -> bool:
        """
        Unsubscribe an agent from a topic.
        
        Args:
            agent_id: Agent identifier
            topic: Topic to unsubscribe from
            
        Returns:
            bool: True if unsubscription successful
        """
        try:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(agent_id)
                
                # Remove topic if no subscribers
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            logger.info(f"??Agent {agent_id} unsubscribed from topic '{topic}'")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to unsubscribe agent {agent_id} from topic '{topic}': {e}")
            return False
    
    async def get_messages(self, agent_id: str, timeout: float = 1.0) -> List[AgentMessage]:
        """
        Get pending messages for an agent.
        
        Args:
            agent_id: Agent identifier
            timeout: Timeout for waiting for messages
            
        Returns:
            List of pending messages
        """
        if agent_id not in self.agent_queues:
            return []
        
        messages = []
        queue = self.agent_queues[agent_id]
        handler = self.message_handlers.get(agent_id)
        
        try:
            # Get all available messages without blocking
            while not queue.empty():
                try:
                    message = queue.get_nowait()
                    messages.append(message)
                    
                    # Call handler if available
                    if handler:
                        try:
                            message_data = message.to_dict()
                            asyncio.create_task(handler(message_data))
                        except Exception as e:
                            logger.error(f"??Error calling handler for agent {agent_id}: {e}")
                            
                except asyncio.QueueEmpty:
                    break
            
            # If no messages and timeout > 0, wait for one message
            if not messages and timeout > 0:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=timeout)
                    messages.append(message)
                    
                    # Call handler if available
                    if handler:
                        try:
                            message_data = message.to_dict()
                            asyncio.create_task(handler(message_data))
                        except Exception as e:
                            logger.error(f"??Error calling handler for agent {agent_id}: {e}")
                            
                except asyncio.TimeoutError:
                    pass
            
        except Exception as e:
            logger.error(f"??Error getting messages for agent {agent_id}: {e}")
        
        return messages
    
    async def acknowledge_message(self, message_id: str, agent_id: str) -> bool:
        """
        Acknowledge receipt of a message.
        
        Args:
            message_id: Message identifier
            agent_id: Agent acknowledging the message
            
        Returns:
            bool: True if acknowledgment successful
        """
        try:
            if message_id in self.delivery_receipts:
                receipt = self.delivery_receipts[message_id]
                receipt.status = MessageStatus.ACKNOWLEDGED
                receipt.acknowledged_at = datetime.now(UTC)
                
                logger.debug(f"??Message {message_id} acknowledged by {agent_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"??Failed to acknowledge message {message_id}: {e}")
            return False
    
    async def _default_message_handler(self, message_data: Dict[str, Any]) -> None:
        """Default message handler for agents without custom handlers"""
        logger.info(f"??¨ Default handler received message: {message_data.get('message_id', 'unknown')}")
    
    async def _process_message_queue(self) -> None:
        """Background task to monitor message queues (messages are retrieved via get_messages)"""
        while True:
            try:
                # Just monitor queue health and log statistics
                total_pending = sum(queue.qsize() for queue in self.agent_queues.values())
                if total_pending > 0:
                    logger.debug(f"?? Total pending messages across all queues: {total_pending}")
                
                # Sleep to prevent busy waiting
                await asyncio.sleep(self.message_process_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"??Error in message processor: {e}")
                await asyncio.sleep(1.0)
    
    async def _cleanup_expired_messages(self) -> None:
        """Background task to cleanup expired messages and receipts"""
        while True:
            try:
                current_time = datetime.now(UTC)
                
                # Cleanup expired routing entries
                expired_routes = [
                    msg_id for msg_id, route in self.routing_table.items()
                    if route.expires_at and route.expires_at < current_time
                ]
                
                for msg_id in expired_routes:
                    del self.routing_table[msg_id]
                    
                    # Mark as expired in delivery receipts
                    if msg_id in self.delivery_receipts:
                        self.delivery_receipts[msg_id].status = MessageStatus.EXPIRED
                
                # Cleanup old delivery receipts (older than 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                expired_receipts = [
                    msg_id for msg_id, receipt in self.delivery_receipts.items()
                    if receipt.delivered_at < cutoff_time
                ]
                
                for msg_id in expired_receipts:
                    del self.delivery_receipts[msg_id]
                
                if expired_routes or expired_receipts:
                    logger.debug(f"?§¹ Cleaned up {len(expired_routes)} expired routes and {len(expired_receipts)} old receipts")
                
                # Sleep for configured interval before next cleanup
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"??Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            Dict containing communication statistics
        """
        return {
            **self.stats,
            "active_queues": len(self.agent_queues),
            "pending_messages": sum(queue.qsize() for queue in self.agent_queues.values()),
            "active_subscriptions": len(self.subscriptions),
            "pending_routes": len(self.routing_table),
            "delivery_receipts": len(self.delivery_receipts)
        }


# Convenience function for creating communication manager
def create_communication_manager(agentcore_client: AgentCoreClient, cleanup_interval: int = 5, message_process_interval: float = 0.1) -> AgentCommunicationManager:
    """
    Create a new agent communication manager.
    
    Args:
        agentcore_client: AgentCore client for message routing
        cleanup_interval: Interval in seconds for cleanup task (default: 5 for testing)
        message_process_interval: Interval in seconds for message processing (default: 0.1)
        
    Returns:
        AgentCommunicationManager: Configured communication manager
    """
    return AgentCommunicationManager(agentcore_client, cleanup_interval, message_process_interval)

# Backward compatibility alias
AgentCommunicationService = AgentCommunicationManager
