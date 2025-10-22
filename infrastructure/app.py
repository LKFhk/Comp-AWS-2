#!/usr/bin/env python3
"""
AWS CDK App for riskintel360 Platform Infrastructure
"""

import aws_cdk as cdk
from infrastructure.stacks.riskintel360_stack import RiskIntel360Stack


app = cdk.App()

# Get environment configuration
env_name = app.node.try_get_context("environment") or "development"
account = app.node.try_get_context("account")
region = app.node.try_get_context("region") or "us-east-1"

# Create the main stack
RiskIntel360Stack(
    app,
    f"RiskIntel360Stack-{env_name}",
    env=cdk.Environment(account=account, region=region),
    environment=env_name,
    description=f"RiskIntel360 Platform Infrastructure - {env_name}",
)

app.synth()
