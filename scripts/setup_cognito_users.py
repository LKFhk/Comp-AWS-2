#!/usr/bin/env python3
"""
Script to set up Cognito users and groups for testing
"""

import boto3
import json
import os
import sys
from typing import Dict, Any
import argparse

def create_cognito_user(
    cognito_client,
    user_pool_id: str,
    username: str,
    email: str,
    password: str,
    tenant_id: str = "default",
    first_name: str = "",
    last_name: str = ""
) -> Dict[str, Any]:
    """Create a Cognito user"""
    try:
        # Create user
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'given_name', 'Value': first_name},
                {'Name': 'family_name', 'Value': last_name},
                {'Name': 'custom:tenant_id', 'Value': tenant_id},
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS',  # Don't send welcome email
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )
        
        print(f"??Created user: {username} ({email})")
        return response
        
    except Exception as e:
        print(f"??Failed to create user {username}: {e}")
        return {}


def add_user_to_group(
    cognito_client,
    user_pool_id: str,
    username: str,
    group_name: str
) -> bool:
    """Add user to Cognito group"""
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"??Added {username} to group: {group_name}")
        return True
        
    except Exception as e:
        print(f"??Failed to add {username} to group {group_name}: {e}")
        return False


def setup_test_users(user_pool_id: str, region: str = "us-east-1"):
    """Set up test users for different roles"""
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    # Test users configuration
    test_users = [
        {
            "username": "admin_user",
            "email": "admin@riskintel360.com",
            "password": "AdminPass123!",
            "first_name": "Admin",
            "last_name": "User",
            "tenant_id": "default",
            "groups": ["admin"]
        },
        {
            "username": "analyst_user",
            "email": "analyst@riskintel360.com",
            "password": "AnalystPass123!",
            "first_name": "Business",
            "last_name": "Analyst",
            "tenant_id": "default",
            "groups": ["analyst"]
        },
        {
            "username": "viewer_user",
            "email": "viewer@riskintel360.com",
            "password": "ViewerPass123!",
            "first_name": "Read",
            "last_name": "Only",
            "tenant_id": "default",
            "groups": ["viewer"]
        },
        {
            "username": "api_user",
            "email": "api@riskintel360.com",
            "password": "ApiPass123!",
            "first_name": "API",
            "last_name": "User",
            "tenant_id": "default",
            "groups": ["api_user"]
        },
        {
            "username": "tenant_user",
            "email": "tenant@company.com",
            "password": "TenantPass123!",
            "first_name": "Tenant",
            "last_name": "User",
            "tenant_id": "company-123",
            "groups": ["analyst"]
        }
    ]
    
    print(f"Setting up test users in User Pool: {user_pool_id}")
    print("=" * 60)
    
    # Create users
    for user_config in test_users:
        # Create user
        create_cognito_user(
            cognito_client=cognito_client,
            user_pool_id=user_pool_id,
            username=user_config["username"],
            email=user_config["email"],
            password=user_config["password"],
            tenant_id=user_config["tenant_id"],
            first_name=user_config["first_name"],
            last_name=user_config["last_name"]
        )
        
        # Add to groups
        for group_name in user_config["groups"]:
            add_user_to_group(
                cognito_client=cognito_client,
                user_pool_id=user_pool_id,
                username=user_config["username"],
                group_name=group_name
            )
        
        print()
    
    print("=" * 60)
    print("??Test user setup complete!")
    print("\nTest Users Created:")
    print("- admin_user (AdminPass123!) - Full admin access")
    print("- analyst_user (AnalystPass123!) - Business analyst access")
    print("- viewer_user (ViewerPass123!) - Read-only access")
    print("- api_user (ApiPass123!) - API programmatic access")
    print("- tenant_user (TenantPass123!) - Multi-tenant test user")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Set up Cognito test users")
    parser.add_argument("--user-pool-id", required=True, help="Cognito User Pool ID")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    
    args = parser.parse_args()
    
    try:
        setup_test_users(args.user_pool_id, args.region)
    except Exception as e:
        print(f"??Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
