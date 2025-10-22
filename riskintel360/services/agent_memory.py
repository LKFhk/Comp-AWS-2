"""
Agent Memory System for RiskIntel360 Platform
Implements hybrid memory system using Redis (local) and ElastiCache (production)
for persistent validation pattern storage and cross-agent knowledge sharing.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import hashlib
import uuid

import redis.asyncio as redis
import boto3
from botocore.exceptions import ClientError

from ..config.settings import get_settings
from ..models.core import ValidationRequest, ValidationResult, AgentMessage, Priority

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"  # Session-based memory
    LONG_TERM = "long_term"    # Persistent across sessions
    SHARED = "shared"          # Cross-agent shared memory
    PATTERN = "pattern"        # Learned patterns and insights
    CACHE = "cache"           # Temporary cached data


class MemoryScope(str, Enum):
    """Scope of memory access"""
    AGENT_PRIVATE = "agent_private"      # Private to specific agent
    AGENT_SHARED = "agent_shared"        # Shared among agent types
    WORKFLOW_SHARED = "workflow_shared"  # Shared within workflow
    GLOBAL_SHARED = "global_shared"      # Globally accessible


@dataclass
class MemoryEntry:
    """Individual memory entry"""
    id: str
    agent_id: str
    memory_type: MemoryType
    scope: MemoryScope
    key: str
    value: Any
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    confidence_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "memory_type": self.memory_type.value,
            "scope": self.scope.value,
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "confidence_score": self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            memory_type=MemoryType(data["memory_type"]),
            scope=MemoryScope(data["scope"]),
            key=data["key"],
            value=data["value"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            access_count=data["access_count"],
            confidence_score=data["confidence_score"]
        )


@dataclass
class ValidationPattern:
    """Learned validation pattern"""
    pattern_id: str
    business_concept_hash: str
    target_market: str
    analysis_results: Dict[str, Any]
    success_indicators: List[str]
    failure_indicators: List[str]
    confidence_score: float
    usage_count: int
    created_at: datetime
    last_used: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["created_at"] = self.created_at.isoformat()
        data["last_used"] = self.last_used.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationPattern":
        """Create from dictionary"""
        return cls(
            pattern_id=data["pattern_id"],
            business_concept_hash=data["business_concept_hash"],
            target_market=data["target_market"],
            analysis_results=data["analysis_results"],
            success_indicators=data["success_indicators"],
            failure_indicators=data["failure_indicators"],
            confidence_score=data["confidence_score"],
            usage_count=data["usage_count"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            last_used=datetime.fromisoformat(data["last_used"]) if isinstance(data["last_used"], str) else data["last_used"]
        )


class MemoryBackend(ABC):
    """Abstract base class for memory backends"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the memory backend"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the memory backend"""
        pass
    
    @abstractmethod
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL"""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value by key"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        pass


class RedisMemoryBackend(MemoryBackend):
    """Redis-based memory backend for local development"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        Initialize Redis backend.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client: Optional[redis.Redis] = None
        
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            logger.info(f"??Connected to Redis at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("??Disconnected from Redis")
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in Redis"""
        try:
            if not self.client:
                return False
            
            # Serialize value
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                await self.client.setex(key, ttl, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"??Failed to store key {key}: {e}")
            return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis"""
        try:
            if not self.client:
                return None
            
            value = await self.client.get(key)
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"??Failed to retrieve key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            if not self.client:
                return False
            
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"??Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            if not self.client:
                return False
            
            return await self.client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"??Failed to check existence of key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if not self.client:
                return []
            
            return await self.client.keys(pattern)
            
        except Exception as e:
            logger.error(f"??Failed to get keys with pattern {pattern}: {e}")
            return []
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.client:
                return False
            
            return await self.client.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"??Failed to set expiration for key {key}: {e}")
            return False


class ElastiCacheMemoryBackend(MemoryBackend):
    """ElastiCache-based memory backend for production"""
    
    def __init__(self, cluster_endpoint: str, port: int = 6379):
        """
        Initialize ElastiCache backend.
        
        Args:
            cluster_endpoint: ElastiCache cluster endpoint
            port: ElastiCache port
        """
        self.cluster_endpoint = cluster_endpoint
        self.port = port
        self.client: Optional[redis.Redis] = None
        
    async def connect(self) -> bool:
        """Connect to ElastiCache"""
        try:
            self.client = redis.Redis(
                host=self.cluster_endpoint,
                port=self.port,
                decode_responses=True,
                ssl=True,  # ElastiCache typically uses SSL
                ssl_cert_reqs=None
            )
            
            # Test connection
            await self.client.ping()
            logger.info(f"??Connected to ElastiCache at {self.cluster_endpoint}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to connect to ElastiCache: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from ElastiCache"""
        if self.client:
            await self.client.close()
            logger.info("??Disconnected from ElastiCache")
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in ElastiCache"""
        try:
            if not self.client:
                return False
            
            # Serialize value
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                await self.client.setex(key, ttl, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"??Failed to store key {key}: {e}")
            return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from ElastiCache"""
        try:
            if not self.client:
                return None
            
            value = await self.client.get(key)
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"??Failed to retrieve key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from ElastiCache"""
        try:
            if not self.client:
                return False
            
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"??Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in ElastiCache"""
        try:
            if not self.client:
                return False
            
            return await self.client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"??Failed to check existence of key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if not self.client:
                return []
            
            return await self.client.keys(pattern)
            
        except Exception as e:
            logger.error(f"??Failed to get keys with pattern {pattern}: {e}")
            return []
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.client:
                return False
            
            return await self.client.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"??Failed to set expiration for key {key}: {e}")
            return False


class SQSMessageQueue:
    """AWS SQS-based message queue for cross-agent knowledge sharing"""
    
    def __init__(self, queue_name: str, region: str = "us-east-1"):
        """
        Initialize SQS message queue.
        
        Args:
            queue_name: SQS queue name
            region: AWS region
        """
        self.queue_name = queue_name
        self.region = region
        self.sqs_client = None
        self.queue_url = None
        
    async def connect(self) -> bool:
        """Connect to SQS"""
        try:
            self.sqs_client = boto3.client('sqs', region_name=self.region)
            
            # Get or create queue
            try:
                response = self.sqs_client.get_queue_url(QueueName=self.queue_name)
                self.queue_url = response['QueueUrl']
            except ClientError as e:
                if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                    # Create queue
                    response = self.sqs_client.create_queue(
                        QueueName=self.queue_name,
                        Attributes={
                            'VisibilityTimeoutSeconds': '300',
                            'MessageRetentionPeriod': '1209600',  # 14 days
                            'DelaySeconds': '0'
                        }
                    )
                    self.queue_url = response['QueueUrl']
                else:
                    raise
            
            logger.info(f"??Connected to SQS queue: {self.queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to connect to SQS: {e}")
            return False
    
    async def send_message(self, message: Dict[str, Any], delay_seconds: int = 0) -> bool:
        """Send message to SQS queue"""
        try:
            if not self.sqs_client or not self.queue_url:
                return False
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message, default=str),
                DelaySeconds=delay_seconds
            )
            
            return 'MessageId' in response
            
        except Exception as e:
            logger.error(f"??Failed to send SQS message: {e}")
            return False
    
    async def receive_messages(self, max_messages: int = 10, wait_time: int = 20) -> List[Dict[str, Any]]:
        """Receive messages from SQS queue"""
        try:
            if not self.sqs_client or not self.queue_url:
                return []
            
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                AttributeNames=['All']
            )
            
            messages = []
            for message in response.get('Messages', []):
                try:
                    body = json.loads(message['Body'])
                    messages.append({
                        'id': message['MessageId'],
                        'receipt_handle': message['ReceiptHandle'],
                        'body': body,
                        'attributes': message.get('Attributes', {})
                    })
                except json.JSONDecodeError:
                    logger.error(f"??Failed to parse SQS message: {message['MessageId']}")
            
            return messages
            
        except Exception as e:
            logger.error(f"??Failed to receive SQS messages: {e}")
            return []
    
    async def delete_message(self, receipt_handle: str) -> bool:
        """Delete message from SQS queue"""
        try:
            if not self.sqs_client or not self.queue_url:
                return False
            
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            
            return True
            
        except Exception as e:
            logger.error(f"??Failed to delete SQS message: {e}")
            return False


class InMemoryMessageQueue:
    """In-memory message queue for local development"""
    
    def __init__(self):
        """Initialize in-memory queue"""
        self.queue: asyncio.Queue = asyncio.Queue()
        self.message_id_counter = 0
        
    async def connect(self) -> bool:
        """Connect (no-op for in-memory)"""
        logger.info("??Connected to in-memory message queue")
        return True
    
    async def send_message(self, message: Dict[str, Any], delay_seconds: int = 0) -> bool:
        """Send message to in-memory queue"""
        try:
            self.message_id_counter += 1
            message_wrapper = {
                'id': str(self.message_id_counter),
                'receipt_handle': str(uuid.uuid4()),
                'body': message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if delay_seconds > 0:
                # Schedule delayed message
                asyncio.create_task(self._delayed_send(message_wrapper, delay_seconds))
            else:
                await self.queue.put(message_wrapper)
            
            return True
            
        except Exception as e:
            logger.error(f"??Failed to send in-memory message: {e}")
            return False
    
    async def receive_messages(self, max_messages: int = 10, wait_time: int = 20) -> List[Dict[str, Any]]:
        """Receive messages from in-memory queue"""
        messages = []
        
        try:
            # Get available messages up to max_messages
            for _ in range(max_messages):
                try:
                    message = await asyncio.wait_for(self.queue.get(), timeout=wait_time if not messages else 0.1)
                    messages.append(message)
                except asyncio.TimeoutError:
                    break
            
        except Exception as e:
            logger.error(f"??Failed to receive in-memory messages: {e}")
        
        return messages
    
    async def delete_message(self, receipt_handle: str) -> bool:
        """Delete message (no-op for in-memory as messages are consumed)"""
        return True
    
    async def _delayed_send(self, message: Dict[str, Any], delay_seconds: int) -> None:
        """Send message after delay"""
        await asyncio.sleep(delay_seconds)
        await self.queue.put(message)


class AgentMemoryManager:
    """
    Hybrid agent memory system with environment-specific backends.
    Manages persistent validation patterns, cross-agent knowledge sharing,
    and intelligent memory retrieval.
    """
    
    def __init__(self):
        """Initialize memory manager"""
        self.settings = get_settings()
        self.backend: Optional[MemoryBackend] = None
        self.message_queue = None
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.validation_patterns: Dict[str, ValidationPattern] = {}
        
        # Memory statistics
        self.stats = {
            "entries_stored": 0,
            "entries_retrieved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "patterns_learned": 0,
            "patterns_applied": 0
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._pattern_learning_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize memory system with environment-specific backend"""
        try:
            # Initialize memory backend based on environment
            if self.settings.environment.value == "development":
                # Use Redis for local development
                self.backend = RedisMemoryBackend(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=int(os.getenv("REDIS_DB", "0")),
                    password=os.getenv("REDIS_PASSWORD")
                )
                
                # Use in-memory queue for local development
                self.message_queue = InMemoryMessageQueue()
                
            else:
                # Use ElastiCache for production
                cluster_endpoint = os.getenv("ELASTICACHE_ENDPOINT")
                if not cluster_endpoint:
                    logger.error("??ELASTICACHE_ENDPOINT not configured for production")
                    return False
                
                self.backend = ElastiCacheMemoryBackend(
                    cluster_endpoint=cluster_endpoint,
                    port=int(os.getenv("ELASTICACHE_PORT", "6379"))
                )
                
                # Use SQS for production
                queue_name = os.getenv("SQS_MEMORY_QUEUE", "RiskIntel360-agent-memory")
                self.message_queue = SQSMessageQueue(
                    queue_name=queue_name,
                    region=os.getenv("AWS_REGION", "us-east-1")
                )
            
            # Connect to backend and message queue
            backend_connected = await self.backend.connect()
            queue_connected = await self.message_queue.connect()
            
            if not backend_connected or not queue_connected:
                logger.error("??Failed to connect to memory backend or message queue")
                return False
            
            # Load existing validation patterns
            await self._load_validation_patterns()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("??Agent memory system initialized")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to initialize memory system: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown memory system"""
        try:
            # Stop background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self._pattern_learning_task:
                self._pattern_learning_task.cancel()
                try:
                    await self._pattern_learning_task
                except asyncio.CancelledError:
                    pass
            
            # Save validation patterns
            await self._save_validation_patterns()
            
            # Disconnect from backend
            if self.backend:
                await self.backend.disconnect()
            
            logger.info("??Agent memory system shutdown")
            
        except Exception as e:
            logger.error(f"??Error during memory system shutdown: {e}") 
   
    async def store_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        confidence_score: float = 1.0
    ) -> str:
        """
        Store a memory entry.
        
        Args:
            agent_id: Agent storing the memory
            memory_type: Type of memory
            scope: Memory access scope
            key: Memory key
            value: Memory value
            metadata: Optional metadata
            ttl: Time to live in seconds
            confidence_score: Confidence in the memory
            
        Returns:
            str: Memory entry ID
        """
        try:
            # Create memory entry
            entry_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            entry = MemoryEntry(
                id=entry_id,
                agent_id=agent_id,
                memory_type=memory_type,
                scope=scope,
                key=key,
                value=value,
                metadata=metadata or {},
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(seconds=ttl) if ttl else None,
                confidence_score=confidence_score
            )
            
            # Generate storage key
            storage_key = self._generate_storage_key(agent_id, memory_type, scope, key)
            
            # Store in backend
            success = await self.backend.store(storage_key, entry.to_dict(), ttl)
            
            if success:
                # Cache locally
                self.memory_cache[storage_key] = entry
                
                # Share knowledge if appropriate
                if scope in [MemoryScope.AGENT_SHARED, MemoryScope.WORKFLOW_SHARED, MemoryScope.GLOBAL_SHARED]:
                    await self._share_knowledge(entry)
                
                self.stats["entries_stored"] += 1
                logger.debug(f"??Stored memory entry {entry_id} for agent {agent_id}")
                return entry_id
            
            return ""
            
        except Exception as e:
            logger.error(f"??Failed to store memory: {e}")
            return ""
    
    async def retrieve_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        key: str
    ) -> Optional[MemoryEntry]:
        """
        Retrieve a memory entry.
        
        Args:
            agent_id: Agent requesting the memory
            memory_type: Type of memory
            scope: Memory access scope
            key: Memory key
            
        Returns:
            MemoryEntry if found, None otherwise
        """
        try:
            storage_key = self._generate_storage_key(agent_id, memory_type, scope, key)
            
            # Check local cache first
            if storage_key in self.memory_cache:
                entry = self.memory_cache[storage_key]
                
                # Check if expired
                if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
                    del self.memory_cache[storage_key]
                    await self.backend.delete(storage_key)
                    return None
                
                # Update access count
                entry.access_count += 1
                entry.updated_at = datetime.now(timezone.utc)
                
                self.stats["cache_hits"] += 1
                self.stats["entries_retrieved"] += 1
                return entry
            
            # Retrieve from backend
            data = await self.backend.retrieve(storage_key)
            if data:
                entry = MemoryEntry.from_dict(data)
                
                # Check if expired
                if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
                    await self.backend.delete(storage_key)
                    return None
                
                # Update access count
                entry.access_count += 1
                entry.updated_at = datetime.now(timezone.utc)
                
                # Cache locally
                self.memory_cache[storage_key] = entry
                
                # Update in backend
                await self.backend.store(storage_key, entry.to_dict())
                
                self.stats["cache_misses"] += 1
                self.stats["entries_retrieved"] += 1
                return entry
            
            return None
            
        except Exception as e:
            logger.error(f"??Failed to retrieve memory: {e}")
            return None
    
    async def search_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        scope: Optional[MemoryScope] = None,
        pattern: str = "*",
        limit: int = 100
    ) -> List[MemoryEntry]:
        """
        Search for memory entries matching criteria.
        
        Args:
            agent_id: Agent performing the search
            memory_type: Optional memory type filter
            scope: Optional scope filter
            pattern: Key pattern to match
            limit: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        try:
            # Build search pattern
            search_pattern = f"memory:{agent_id}:"
            if memory_type:
                search_pattern += f"{memory_type.value}:"
            else:
                search_pattern += "*:"
            
            if scope:
                search_pattern += f"{scope.value}:"
            else:
                search_pattern += "*:"
            
            search_pattern += pattern
            
            # Get matching keys
            keys = await self.backend.keys(search_pattern)
            
            # Retrieve entries
            entries = []
            for key in keys[:limit]:
                data = await self.backend.retrieve(key)
                if data:
                    try:
                        entry = MemoryEntry.from_dict(data)
                        
                        # Check if expired
                        if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
                            await self.backend.delete(key)
                            continue
                        
                        entries.append(entry)
                    except Exception as e:
                        logger.error(f"??Failed to parse memory entry {key}: {e}")
            
            return entries
            
        except Exception as e:
            logger.error(f"??Failed to search memories: {e}")
            return []
    
    async def delete_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        key: str
    ) -> bool:
        """
        Delete a memory entry.
        
        Args:
            agent_id: Agent deleting the memory
            memory_type: Type of memory
            scope: Memory access scope
            key: Memory key
            
        Returns:
            bool: True if deletion successful
        """
        try:
            storage_key = self._generate_storage_key(agent_id, memory_type, scope, key)
            
            # Delete from backend
            success = await self.backend.delete(storage_key)
            
            # Remove from cache
            if storage_key in self.memory_cache:
                del self.memory_cache[storage_key]
            
            if success:
                logger.debug(f"??Deleted memory entry {storage_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"??Failed to delete memory: {e}")
            return False
    
    async def learn_validation_pattern(
        self,
        validation_request: ValidationRequest,
        validation_result: ValidationResult
    ) -> str:
        """
        Learn a validation pattern from completed validation.
        
        Args:
            validation_request: Original validation request
            validation_result: Validation results
            
        Returns:
            str: Pattern ID if learning successful
        """
        try:
            # Generate pattern hash from business concept
            concept_hash = hashlib.sha256(
                validation_request.business_concept.lower().encode()
            ).hexdigest()[:16]
            
            # Extract success/failure indicators
            success_indicators = []
            failure_indicators = []
            
            if validation_result.overall_score >= 70:
                success_indicators.extend([
                    f"market_confidence_{validation_result.market_analysis.confidence_score if validation_result.market_analysis else 0}",
                    f"financial_viability_{validation_result.financial_analysis.viability_score if validation_result.financial_analysis else 0}",
                    f"overall_score_{validation_result.overall_score}"
                ])
            else:
                failure_indicators.extend([
                    f"low_market_confidence_{validation_result.market_analysis.confidence_score if validation_result.market_analysis else 0}",
                    f"poor_financial_viability_{validation_result.financial_analysis.viability_score if validation_result.financial_analysis else 0}",
                    f"low_overall_score_{validation_result.overall_score}"
                ])
            
            # Create validation pattern
            pattern_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            pattern = ValidationPattern(
                pattern_id=pattern_id,
                business_concept_hash=concept_hash,
                target_market=validation_request.target_market,
                analysis_results={
                    "overall_score": validation_result.overall_score,
                    "confidence_level": validation_result.confidence_level,
                    "market_analysis": validation_result.market_analysis.model_dump() if validation_result.market_analysis else None,
                    "competitive_analysis": validation_result.competitive_analysis.model_dump() if validation_result.competitive_analysis else None,
                    "financial_analysis": validation_result.financial_analysis.model_dump() if validation_result.financial_analysis else None,
                    "risk_analysis": validation_result.risk_analysis.model_dump() if validation_result.risk_analysis else None,
                    "customer_analysis": validation_result.customer_analysis.model_dump() if validation_result.customer_analysis else None
                },
                success_indicators=success_indicators,
                failure_indicators=failure_indicators,
                confidence_score=validation_result.confidence_level,
                usage_count=0,
                created_at=now,
                last_used=now
            )
            
            # Store pattern
            self.validation_patterns[pattern_id] = pattern
            
            # Store in persistent memory
            await self.store_memory(
                agent_id="system",
                memory_type=MemoryType.PATTERN,
                scope=MemoryScope.GLOBAL_SHARED,
                key=f"validation_pattern_{concept_hash}",
                value=pattern.to_dict(),
                metadata={
                    "target_market": validation_request.target_market,
                    "analysis_scope": validation_request.analysis_scope,
                    "created_from_request": validation_request.id
                }
            )
            
            self.stats["patterns_learned"] += 1
            logger.info(f"??Learned validation pattern {pattern_id} from request {validation_request.id}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"??Failed to learn validation pattern: {e}")
            return ""
    
    async def find_similar_patterns(
        self,
        business_concept: str,
        target_market: str,
        limit: int = 5
    ) -> List[ValidationPattern]:
        """
        Find similar validation patterns for a business concept.
        
        Args:
            business_concept: Business concept to match
            target_market: Target market
            limit: Maximum number of patterns to return
            
        Returns:
            List of similar validation patterns
        """
        try:
            concept_hash = hashlib.sha256(
                business_concept.lower().encode()
            ).hexdigest()[:16]
            
            # Search for exact match first
            exact_matches = [
                pattern for pattern in self.validation_patterns.values()
                if pattern.business_concept_hash == concept_hash
            ]
            
            if exact_matches:
                # Sort by usage count and confidence
                exact_matches.sort(
                    key=lambda p: (p.usage_count, p.confidence_score),
                    reverse=True
                )
                return exact_matches[:limit]
            
            # Search for similar target markets
            similar_patterns = [
                pattern for pattern in self.validation_patterns.values()
                if pattern.target_market.lower() == target_market.lower()
            ]
            
            # Sort by confidence and usage
            similar_patterns.sort(
                key=lambda p: (p.confidence_score, p.usage_count),
                reverse=True
            )
            
            return similar_patterns[:limit]
            
        except Exception as e:
            logger.error(f"??Failed to find similar patterns: {e}")
            return []
    
    async def apply_pattern_insights(
        self,
        pattern: ValidationPattern,
        current_request: ValidationRequest
    ) -> Dict[str, Any]:
        """
        Apply insights from a validation pattern to current request.
        
        Args:
            pattern: Validation pattern to apply
            current_request: Current validation request
            
        Returns:
            Dict containing pattern insights
        """
        try:
            # Update pattern usage
            pattern.usage_count += 1
            pattern.last_used = datetime.now(timezone.utc)
            
            # Extract insights
            insights = {
                "pattern_id": pattern.pattern_id,
                "confidence_score": pattern.confidence_score,
                "usage_count": pattern.usage_count,
                "success_indicators": pattern.success_indicators,
                "failure_indicators": pattern.failure_indicators,
                "historical_results": {
                    "overall_score": pattern.analysis_results.get("overall_score"),
                    "confidence_level": pattern.analysis_results.get("confidence_level")
                },
                "recommendations": []
            }
            
            # Generate recommendations based on pattern
            if pattern.success_indicators:
                insights["recommendations"].append({
                    "type": "success_factors",
                    "description": "Focus on factors that led to success in similar validations",
                    "factors": pattern.success_indicators
                })
            
            if pattern.failure_indicators:
                insights["recommendations"].append({
                    "type": "risk_mitigation",
                    "description": "Address factors that led to failure in similar validations",
                    "factors": pattern.failure_indicators
                })
            
            # Add market-specific insights
            if pattern.analysis_results.get("market_analysis"):
                market_data = pattern.analysis_results["market_analysis"]
                insights["market_insights"] = {
                    "historical_confidence": market_data.get("confidence_score"),
                    "key_trends": market_data.get("growth_trends", []),
                    "entry_barriers": market_data.get("entry_barriers", [])
                }
            
            self.stats["patterns_applied"] += 1
            logger.info(f"??Applied pattern {pattern.pattern_id} to request {current_request.id}")
            return insights
            
        except Exception as e:
            logger.error(f"??Failed to apply pattern insights: {e}")
            return {}
    
    async def share_knowledge(
        self,
        sender_agent_id: str,
        knowledge_type: str,
        knowledge_data: Dict[str, Any],
        target_agents: Optional[List[str]] = None
    ) -> bool:
        """
        Share knowledge between agents.
        
        Args:
            sender_agent_id: Agent sharing the knowledge
            knowledge_type: Type of knowledge being shared
            knowledge_data: Knowledge data to share
            target_agents: Optional list of target agents (None for broadcast)
            
        Returns:
            bool: True if sharing successful
        """
        try:
            message = {
                "type": "knowledge_sharing",
                "sender_agent_id": sender_agent_id,
                "knowledge_type": knowledge_type,
                "knowledge_data": knowledge_data,
                "target_agents": target_agents,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid.uuid4())
            }
            
            success = await self.message_queue.send_message(message)
            
            if success:
                logger.info(f"??Knowledge shared by {sender_agent_id}: {knowledge_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"??Failed to share knowledge: {e}")
            return False
    
    async def receive_shared_knowledge(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Receive shared knowledge for an agent.
        
        Args:
            agent_id: Agent receiving knowledge
            
        Returns:
            List of knowledge messages
        """
        try:
            messages = await self.message_queue.receive_messages(max_messages=10, wait_time=1)
            
            relevant_messages = []
            for message in messages:
                body = message['body']
                
                # Check if message is relevant to this agent
                target_agents = body.get('target_agents')
                if target_agents is None or agent_id in target_agents:
                    relevant_messages.append(body)
                
                # Delete processed message
                await self.message_queue.delete_message(message['receipt_handle'])
            
            return relevant_messages
            
        except Exception as e:
            logger.error(f"??Failed to receive shared knowledge: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dict containing memory statistics
        """
        return {
            **self.stats,
            "cached_entries": len(self.memory_cache),
            "validation_patterns": len(self.validation_patterns),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
            ) * 100
        }
    
    def _generate_storage_key(
        self,
        agent_id: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        key: str
    ) -> str:
        """Generate storage key for memory entry"""
        return f"memory:{agent_id}:{memory_type.value}:{scope.value}:{key}"
    
    async def _share_knowledge(self, entry: MemoryEntry) -> None:
        """Share knowledge entry with other agents"""
        try:
            if entry.scope == MemoryScope.AGENT_PRIVATE:
                return
            
            knowledge_data = {
                "entry_id": entry.id,
                "memory_type": entry.memory_type.value,
                "key": entry.key,
                "value": entry.value,
                "metadata": entry.metadata,
                "confidence_score": entry.confidence_score,
                "created_at": entry.created_at.isoformat()
            }
            
            await self.share_knowledge(
                sender_agent_id=entry.agent_id,
                knowledge_type="memory_entry",
                knowledge_data=knowledge_data
            )
            
        except Exception as e:
            logger.error(f"??Failed to share knowledge for entry {entry.id}: {e}")
    
    async def _load_validation_patterns(self) -> None:
        """Load existing validation patterns from storage"""
        try:
            # Search for pattern entries
            pattern_entries = await self.search_memories(
                agent_id="system",
                memory_type=MemoryType.PATTERN,
                scope=MemoryScope.GLOBAL_SHARED,
                pattern="validation_pattern_*"
            )
            
            for entry in pattern_entries:
                try:
                    pattern = ValidationPattern.from_dict(entry.value)
                    self.validation_patterns[pattern.pattern_id] = pattern
                except Exception as e:
                    logger.error(f"??Failed to load validation pattern {entry.id}: {e}")
            
            logger.info(f"??Loaded {len(self.validation_patterns)} validation patterns")
            
        except Exception as e:
            logger.error(f"??Failed to load validation patterns: {e}")
    
    async def _save_validation_patterns(self) -> None:
        """Save validation patterns to storage"""
        try:
            for pattern in self.validation_patterns.values():
                concept_hash = pattern.business_concept_hash
                await self.store_memory(
                    agent_id="system",
                    memory_type=MemoryType.PATTERN,
                    scope=MemoryScope.GLOBAL_SHARED,
                    key=f"validation_pattern_{concept_hash}",
                    value=pattern.to_dict(),
                    metadata={
                        "target_market": pattern.target_market,
                        "usage_count": pattern.usage_count,
                        "last_used": pattern.last_used.isoformat()
                    }
                )
            
            logger.info(f"??Saved {len(self.validation_patterns)} validation patterns")
            
        except Exception as e:
            logger.error(f"??Failed to save validation patterns: {e}")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks"""
        try:
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
            
            # Start pattern learning task
            self._pattern_learning_task = asyncio.create_task(self._pattern_learning_worker())
            
            logger.info("??Memory system background tasks started")
            
        except Exception as e:
            logger.error(f"??Failed to start background tasks: {e}")
    
    async def _cleanup_expired_entries(self) -> None:
        """Background task to cleanup expired memory entries"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                expired_keys = []
                
                # Check cached entries
                for key, entry in list(self.memory_cache.items()):
                    if entry.expires_at and entry.expires_at < current_time:
                        expired_keys.append(key)
                
                # Remove expired entries
                for key in expired_keys:
                    del self.memory_cache[key]
                    await self.backend.delete(key)
                
                if expired_keys:
                    logger.debug(f"?§¹ Cleaned up {len(expired_keys)} expired memory entries")
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"??Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def _pattern_learning_worker(self) -> None:
        """Background task for pattern learning and optimization"""
        while True:
            try:
                # Optimize patterns based on usage
                for pattern in list(self.validation_patterns.values()):
                    # Decay confidence for unused patterns
                    days_since_use = (datetime.now(timezone.utc) - pattern.last_used).days
                    if days_since_use > 30:
                        pattern.confidence_score *= 0.95  # Decay confidence
                        
                        # Remove patterns with very low confidence
                        if pattern.confidence_score < 0.1:
                            del self.validation_patterns[pattern.pattern_id]
                            logger.debug(f"??ï¸?Removed low-confidence pattern {pattern.pattern_id}")
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"??Error in pattern learning worker: {e}")
                await asyncio.sleep(300)


# Import os for environment variables
import os


# Convenience function for creating memory manager
def create_memory_manager() -> AgentMemoryManager:
    """
    Create a new agent memory manager.
    
    Returns:
        AgentMemoryManager: Configured memory manager
    """
    return AgentMemoryManager()
# Global memory manager instance
_memory_manager: Optional[AgentMemoryManager] = None


async def get_memory_manager() -> AgentMemoryManager:
    """
    Get or create the global memory manager instance.
    
    Returns:
        AgentMemoryManager: The global memory manager instance
    """
    global _memory_manager
    
    if _memory_manager is None:
        _memory_manager = AgentMemoryManager()
        success = await _memory_manager.initialize()
        if not success:
            raise RuntimeError("Failed to initialize memory manager")
    
    return _memory_manager


async def shutdown_memory_manager() -> None:
    """Shutdown the global memory manager"""
    global _memory_manager
    
    if _memory_manager is not None:
        await _memory_manager.shutdown()
        _memory_manager = None


# Add missing import for os
import os
