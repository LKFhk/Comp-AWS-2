"""
Tests for CDK infrastructure stack
"""

import aws_cdk as core
import aws_cdk.assertions as assertions
from infrastructure.stacks.riskintel360_stack import RiskIntel360Stack


def test_stack_creation():
    """Test that the stack can be created without errors"""
    app = core.App()
    stack = RiskIntel360Stack(
        app, 
        "TestRiskIntel360Stack",
        environment="testing"
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify VPC is created
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16"
    })
    
    # Verify DynamoDB tables are created
    template.resource_count_is("AWS::DynamoDB::Table", 4)
    
    # Verify Aurora cluster is created
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql"
    })
    
    # Verify S3 buckets are created
    template.resource_count_is("AWS::S3::Bucket", 2)
    
    # Verify ECS cluster is created
    template.has_resource_properties("AWS::ECS::Cluster", {})
    
    # Verify API Gateway is created
    template.has_resource_properties("AWS::ApiGateway::RestApi", {})
