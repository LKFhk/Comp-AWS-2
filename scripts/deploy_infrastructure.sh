#!/bin/bash
set -e

echo "Deploying RiskIntel360 infrastructure..."

# Bootstrap CDK if needed
cdk bootstrap --context environment=$1

# Deploy stack
cdk deploy --context environment=$1 --require-approval never

echo "Deployment completed successfully"
