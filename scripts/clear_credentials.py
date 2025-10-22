#!/usr/bin/env python3
"""
Clear all stored credentials and reset the system for new users.
This script removes all encrypted credential files and resets the system to show 0 credentials.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from riskintel360.services.credential_manager import credential_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_all_credentials():
    """Clear all stored credentials and reset the system"""
    try:
        # Remove the encrypted credentials file
        credentials_file = ".RiskIntel360_credentials.enc"
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
            logger.info(f"Removed credentials file: {credentials_file}")
        else:
            logger.info(f"Credentials file not found: {credentials_file}")
        
        # Clear the in-memory cache
        if hasattr(credential_manager, '_credentials_cache'):
            credential_manager._credentials_cache.clear()
            logger.info("Cleared credentials cache")
        
        # Verify no credentials remain
        try:
            services = await credential_manager.list_services()
            if services:
                logger.warning(f"Some services still found: {services}")
                # Try to delete each service
                for service in services:
                    success = await credential_manager.delete_credential(service)
                    if success:
                        logger.info(f"Deleted credential for service: {service}")
                    else:
                        logger.warning(f"Failed to delete credential for service: {service}")
            else:
                logger.info("No credentials found - system is clean")
        except Exception as e:
            logger.info(f"No credentials to list (expected): {e}")
        
        logger.info("✅ Credentials cleared successfully!")
        logger.info("The system now shows 0 credentials and is ready for new user setup.")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear credentials: {e}")
        return False

async def main():
    """Main function to clear credentials"""
    logger.info("🧹 Clearing all stored credentials...")
    
    success = await clear_all_credentials()
    
    if success:
        logger.info("🎉 System reset complete! New users can now set up their credentials.")
        return 0
    else:
        logger.error("❌ Failed to clear credentials completely.")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)