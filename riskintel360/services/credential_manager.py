"""
Secure Credential Management Service for RiskIntel360 Platform
Handles API keys, AWS credentials, and other sensitive data with encryption.
"""

import os
import json
import base64
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

@dataclass
class CredentialConfig:
    """Credential configuration"""
    service_name: str
    api_key: str
    region: str
    endpoint_url: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class SecureCredentialManager:
    """Secure credential management with encryption at rest"""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize credential manager with encryption"""
        self.master_key = master_key or os.getenv('RiskIntel360_MASTER_KEY', 'default-dev-key-change-in-prod')
        self.cipher_suite = self._initialize_encryption()
        self.credentials_file = os.getenv('RiskIntel360_CREDENTIALS_FILE', '.RiskIntel360_credentials.enc')
        self._credentials_cache = {}
        
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher"""
        # Derive key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'RiskIntel360_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    async def store_credential(self, service_name: str, key_type_or_config, value=None):
        """Store encrypted credential - supports both old and new API"""
        try:
            # Handle both API styles
            if isinstance(key_type_or_config, CredentialConfig):
                # New API: store_credential(service_name, credential_config)
                credential_config = key_type_or_config
            else:
                # Old API: store_credential(service, key_type, value)
                key_type = key_type_or_config
                credential_config = CredentialConfig(
                    service_name=service_name,
                    api_key=value,
                    region="us-east-1",
                    additional_config={'key_type': key_type}
                )
            
            # Load existing credentials
            credentials = self._load_credentials()
            
            # Add new credential
            credentials[service_name] = {
                'service_name': credential_config.service_name,
                'api_key': credential_config.api_key,
                'region': credential_config.region,
                'endpoint_url': credential_config.endpoint_url,
                'additional_config': credential_config.additional_config or {}
            }
            
            # Save encrypted credentials
            self._save_credentials(credentials)
            
            # Update cache
            self._credentials_cache[service_name] = credential_config
            
            logger.info(f"Stored credential for service: {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to store credential for {service_name}: {e}")
            raise
    
    async def retrieve_credential(self, service_name: str, key_type: str) -> Optional[str]:
        """Retrieve credential value by service and key type"""
        config = self.get_credential(service_name)
        if config and config.additional_config.get('key_type') == key_type:
            return config.api_key
        return None
    
    def get_credential(self, service_name: str) -> Optional[CredentialConfig]:
        """Retrieve and decrypt credential"""
        try:
            # Check cache first
            if service_name in self._credentials_cache:
                return self._credentials_cache[service_name]
            
            # Load from encrypted file
            credentials = self._load_credentials()
            
            if service_name not in credentials:
                return None
            
            cred_data = credentials[service_name]
            config = CredentialConfig(
                service_name=cred_data['service_name'],
                api_key=cred_data['api_key'],
                region=cred_data['region'],
                endpoint_url=cred_data.get('endpoint_url'),
                additional_config=cred_data.get('additional_config', {})
            )
            
            # Cache for future use
            self._credentials_cache[service_name] = config
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential for {service_name}: {e}")
            return None
    
    async def list_services(self) -> list[str]:
        """List all stored service names"""
        try:
            credentials = self._load_credentials()
            return list(credentials.keys())
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    async def delete_credential(self, service_name: str, key_type: str = None) -> bool:
        """Delete a stored credential"""
        try:
            credentials = self._load_credentials()
            
            if service_name in credentials:
                # If key_type is specified, check if it matches
                if key_type is not None:
                    stored_cred = credentials[service_name]
                    stored_key_type = stored_cred.get('additional_config', {}).get('key_type')
                    if stored_key_type != key_type:
                        return False
                
                del credentials[service_name]
                self._save_credentials(credentials)
                
                # Remove from cache
                if service_name in self._credentials_cache:
                    del self._credentials_cache[service_name]
                
                logger.info(f"Deleted credential for service: {service_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete credential for {service_name}: {e}")
            return False
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load and decrypt credentials from file"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return {}
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, Any]):
        """Encrypt and save credentials to file"""
        try:
            json_data = json.dumps(credentials, indent=2)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
    
    def setup_aws_credentials(
        self, 
        access_key_id: str, 
        secret_access_key: str, 
        region: str = 'us-east-1'
    ):
        """Setup AWS credentials"""
        config = CredentialConfig(
            service_name='aws',
            api_key=access_key_id,
            region=region,
            additional_config={
                'secret_access_key': secret_access_key,
                'service_type': 'aws'
            }
        )
        self.store_credential('aws', config)
    
    def setup_bedrock_credentials(
        self, 
        access_key_id: str, 
        secret_access_key: str, 
        region: str = 'us-east-1'
    ):
        """Setup Amazon Bedrock credentials"""
        config = CredentialConfig(
            service_name='bedrock',
            api_key=access_key_id,
            region=region,
            additional_config={
                'secret_access_key': secret_access_key,
                'service_type': 'bedrock'
            }
        )
        self.store_credential('bedrock', config)
    
    def get_aws_config(self) -> Optional[Dict[str, str]]:
        """Get AWS configuration for boto3"""
        aws_cred = self.get_credential('aws')
        if not aws_cred:
            # Fallback to environment variables
            return {
                'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            }
        
        return {
            'aws_access_key_id': aws_cred.api_key,
            'aws_secret_access_key': aws_cred.additional_config.get('secret_access_key'),
            'region_name': aws_cred.region
        }
    
    def get_bedrock_config(self) -> Optional[Dict[str, str]]:
        """Get Bedrock configuration"""
        bedrock_cred = self.get_credential('bedrock')
        if not bedrock_cred:
            # Fallback to AWS credentials
            return self.get_aws_config()
        
        return {
            'aws_access_key_id': bedrock_cred.api_key,
            'aws_secret_access_key': bedrock_cred.additional_config.get('secret_access_key'),
            'region_name': bedrock_cred.region
        }
    
    def validate_credentials(self, service_name: str) -> bool:
        """Validate that credentials exist and are properly formatted"""
        config = self.get_credential(service_name)
        if not config:
            return False
        
        # Basic validation
        if not config.api_key or not config.region:
            return False
        
        # Service-specific validation
        if service_name in ['aws', 'bedrock']:
            additional_config = config.additional_config or {}
            if not additional_config.get('secret_access_key'):
                return False
        
        # For other services, just check if api_key exists and is not empty
        if len(config.api_key.strip()) == 0:
            return False
        
        return True

# Global credential manager instance
credential_manager = SecureCredentialManager()
