"""
Command Line Interface for RiskIntel360 Platform
"""

import argparse
import sys
from typing import List, Optional


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="RiskIntel360",
        description="RiskIntel360 Platform - Autonomous Multi-Agent Business Intelligence",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy infrastructure")
    deploy_parser.add_argument("--environment", default="development", 
                              choices=["development", "staging", "production"],
                              help="Deployment environment")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation")
    validate_parser.add_argument("concept", help="Business concept to validate")
    validate_parser.add_argument("--market", help="Target market")
    validate_parser.add_argument("--scope", nargs="+", 
                                choices=["market", "competitive", "financial", "risk", "customer"],
                                default=["market", "competitive", "financial", "risk", "customer"],
                                help="Analysis scope")
    
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    if parsed_args.command == "server":
        return _start_server(parsed_args)
    elif parsed_args.command == "deploy":
        return _deploy_infrastructure(parsed_args)
    elif parsed_args.command == "validate":
        return _run_validation(parsed_args)
    
    return 0


def _start_server(args) -> int:
    """Start the API server"""
    try:
        import uvicorn
        uvicorn.run(
            "riskintel360.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return 0
    except ImportError:
        print("Error: uvicorn not installed. Run: pip install uvicorn")
        return 1
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1


def _deploy_infrastructure(args) -> int:
    """Deploy infrastructure using CDK"""
    try:
        import subprocess
        result = subprocess.run([
            "cdk", "deploy", 
            "--context", f"environment={args.environment}"
        ], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error deploying infrastructure: {e}")
        return 1
    except FileNotFoundError:
        print("Error: AWS CDK not installed. Run: npm install -g aws-cdk")
        return 1


def _run_validation(args) -> int:
    """Run a validation request"""
    print(f"Running validation for: {args.concept}")
    print(f"Target market: {args.market}")
    print(f"Analysis scope: {', '.join(args.scope)}")
    
    # TODO: Implement actual validation logic
    print("Validation functionality will be implemented in future tasks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
