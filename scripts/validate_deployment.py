#!/usr/bin/env python3
"""
Final deployment validation script for RiskIntel360
Validates all infrastructure and deployment components are properly configured
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple


class DeploymentValidator:
    """Validate RiskIntel360 deployment configuration"""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 RiskIntel360 Deployment Validation")
        print("=" * 50)
        
        validations = [
            ("Infrastructure Files", self._validate_infrastructure_files),
            ("Docker Configuration", self._validate_docker_configuration),
            ("Environment Configuration", self._validate_environment_configuration),
            ("ML Dependencies", self._validate_ml_dependencies),
            ("Fintech Configuration", self._validate_fintech_configuration),
            ("AWS CDK Configuration", self._validate_cdk_configuration),
            ("Test Suite", self._validate_test_suite),
            ("Deployment Scripts", self._validate_deployment_scripts),
            ("Security Configuration", self._validate_security_configuration),
            ("Performance Configuration", self._validate_performance_configuration)
        ]
        
        all_passed = True
        
        for validation_name, validation_func in validations:
            print(f"\n📋 Validating {validation_name}...")
            
            try:
                success, details = validation_func()
                self.validation_results[validation_name] = {
                    "success": success,
                    "details": details
                }
                
                if success:
                    print(f"   ✅ {validation_name}: PASSED")
                else:
                    print(f"   ❌ {validation_name}: FAILED")
                    print(f"      {details}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   💥 {validation_name}: ERROR - {str(e)}")
                self.errors.append(f"{validation_name}: {str(e)}")
                all_passed = False
        
        # Generate final report
        self._generate_validation_report()
        
        return all_passed
    
    def _validate_infrastructure_files(self) -> Tuple[bool, str]:
        """Validate infrastructure files are present and valid"""
        required_files = [
            "infrastructure/app.py",
            "infrastructure/stacks/riskintel360_stack.py",
            "infrastructure/requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "requirements.txt",
            "requirements-ml.txt"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            return False, f"Missing files: {', '.join(missing_files)}"
        
        # Validate CDK stack has fintech resources
        stack_file = self.project_root / "infrastructure/stacks/riskintel360_stack.py"
        with open(stack_file, 'r') as f:
            stack_content = f.read()
        
        fintech_components = [
            "_create_fintech_resources",
            "_create_ml_infrastructure", 
            "_create_cost_monitoring",
            "_create_demo_resources"
        ]
        
        missing_components = []
        for component in fintech_components:
            if component not in stack_content:
                missing_components.append(component)
        
        if missing_components:
            return False, f"Missing fintech components: {', '.join(missing_components)}"
        
        return True, "All infrastructure files present and valid"
    
    def _validate_docker_configuration(self) -> Tuple[bool, str]:
        """Validate Docker configuration"""
        # Check Dockerfile has ML dependencies
        dockerfile = self.project_root / "Dockerfile"
        with open(dockerfile, 'r') as f:
            dockerfile_content = f.read()
        
        required_dockerfile_elements = [
            "requirements-ml.txt",
            "libopenblas-dev",
            "liblapack-dev",
            "target=development",
            "target=production"
        ]
        
        missing_elements = []
        for element in required_dockerfile_elements:
            if element not in dockerfile_content:
                missing_elements.append(element)
        
        if missing_elements:
            return False, f"Dockerfile missing elements: {', '.join(missing_elements)}"
        
        # Check docker-compose has fintech environment variables
        compose_file = self.project_root / "docker-compose.yml"
        with open(compose_file, 'r') as f:
            compose_content = f.read()
        
        required_env_vars = [
            "ALPHA_VANTAGE_API_KEY",
            "BEDROCK_REGION",
            "ML_MODEL_PATH",
            "FRAUD_DETECTION_THRESHOLD"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if var not in compose_content:
                missing_vars.append(var)
        
        if missing_vars:
            return False, f"docker-compose missing env vars: {', '.join(missing_vars)}"
        
        return True, "Docker configuration valid"
    
    def _validate_environment_configuration(self) -> Tuple[bool, str]:
        """Validate environment configuration files"""
        env_files = [".env.example", ".env.development", ".env.production"]
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if not env_path.exists():
                return False, f"Missing environment file: {env_file}"
            
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Check for fintech-specific variables
            fintech_vars = [
                "BEDROCK_REGION",
                "ML_MODEL_PATH", 
                "FRAUD_DETECTION_THRESHOLD",
                "BEDROCK_MODEL_REGULATORY",
                "BEDROCK_MODEL_FRAUD"
            ]
            
            missing_vars = []
            for var in fintech_vars:
                if var not in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                return False, f"{env_file} missing fintech vars: {', '.join(missing_vars)}"
        
        return True, "Environment configuration valid"
    
    def _validate_ml_dependencies(self) -> Tuple[bool, str]:
        """Validate ML dependencies configuration"""
        ml_requirements = self.project_root / "requirements-ml.txt"
        
        if not ml_requirements.exists():
            return False, "requirements-ml.txt not found"
        
        with open(ml_requirements, 'r') as f:
            ml_content = f.read()
        
        required_ml_libs = [
            "scikit-learn",
            "numpy",
            "pandas",
            "tensorflow",
            "torch",
            "pyod",
            "yfinance",
            "alpha-vantage"
        ]
        
        missing_libs = []
        for lib in required_ml_libs:
            if lib not in ml_content:
                missing_libs.append(lib)
        
        if missing_libs:
            return False, f"Missing ML libraries: {', '.join(missing_libs)}"
        
        return True, "ML dependencies configuration valid"
    
    def _validate_fintech_configuration(self) -> Tuple[bool, str]:
        """Validate fintech-specific configuration"""
        # Check if fintech data directories are configured
        data_dirs = [
            "data/regulatory",
            "data/market",
            "data/transactions",
            "models/fraud_detection",
            "demo/data"
        ]
        
        # Create directories if they don't exist (for validation)
        for data_dir in data_dirs:
            dir_path = self.project_root / data_dir
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Check fintech API configuration in environment
        env_example = self.project_root / ".env.example"
        with open(env_example, 'r') as f:
            env_content = f.read()
        
        fintech_apis = [
            "ALPHA_VANTAGE_API_KEY",
            "YAHOO_FINANCE_API_KEY",
            "FRED_API_KEY",
            "SEC_EDGAR_API_KEY",
            "TREASURY_API_KEY"
        ]
        
        missing_apis = []
        for api in fintech_apis:
            if api not in env_content:
                missing_apis.append(api)
        
        if missing_apis:
            return False, f"Missing fintech API configs: {', '.join(missing_apis)}"
        
        return True, "Fintech configuration valid"
    
    def _validate_cdk_configuration(self) -> Tuple[bool, str]:
        """Validate AWS CDK configuration"""
        cdk_app = self.project_root / "infrastructure/app.py"
        
        if not cdk_app.exists():
            return False, "CDK app.py not found"
        
        with open(cdk_app, 'r') as f:
            cdk_content = f.read()
        
        required_cdk_elements = [
            "RiskIntel360Stack",
            "environment=env_name",
            "cdk.Environment"
        ]
        
        missing_elements = []
        for element in required_cdk_elements:
            if element not in cdk_content:
                missing_elements.append(element)
        
        if missing_elements:
            return False, f"CDK app missing elements: {', '.join(missing_elements)}"
        
        # Check if CDK can synthesize (basic syntax check)
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                "import sys; sys.path.append('infrastructure'); import app"
            ], capture_output=True, text=True, timeout=30, cwd=self.project_root)
            
            if result.returncode != 0:
                return False, f"CDK app syntax error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "CDK app validation timeout"
        except Exception as e:
            return False, f"CDK app validation error: {str(e)}"
        
        return True, "CDK configuration valid"
    
    def _validate_test_suite(self) -> Tuple[bool, str]:
        """Validate test suite configuration"""
        test_files = [
            "tests/infrastructure/test_cdk_deployment.py",
            "tests/integration/test_docker_orchestration.py",
            "tests/deployment/test_deployment_validation.py",
            "tests/run_infrastructure_tests.py"
        ]
        
        missing_tests = []
        for test_file in test_files:
            test_path = self.project_root / test_file
            if not test_path.exists():
                missing_tests.append(test_file)
        
        if missing_tests:
            return False, f"Missing test files: {', '.join(missing_tests)}"
        
        # Check test runner is executable
        test_runner = self.project_root / "tests/run_infrastructure_tests.py"
        with open(test_runner, 'r') as f:
            runner_content = f.read()
        
        if "InfrastructureTestRunner" not in runner_content:
            return False, "Test runner not properly configured"
        
        return True, "Test suite configuration valid"
    
    def _validate_deployment_scripts(self) -> Tuple[bool, str]:
        """Validate deployment scripts"""
        deployment_scripts = [
            "scripts/deploy_infrastructure.sh",
            "scripts/deploy_docker.sh",
            "scripts/validate_deployment.py"
        ]
        
        missing_scripts = []
        for script in deployment_scripts:
            script_path = self.project_root / script
            if not script_path.exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            return False, f"Missing deployment scripts: {', '.join(missing_scripts)}"
        
        # Check scripts have proper content
        infra_script = self.project_root / "scripts/deploy_infrastructure.sh"
        with open(infra_script, 'r') as f:
            infra_content = f.read()
        
        if "cdk deploy" not in infra_content:
            return False, "Infrastructure deployment script missing CDK deploy"
        
        docker_script = self.project_root / "scripts/deploy_docker.sh"
        with open(docker_script, 'r') as f:
            docker_content = f.read()
        
        if "docker-compose" not in docker_content:
            return False, "Docker deployment script missing docker-compose"
        
        return True, "Deployment scripts valid"
    
    def _validate_security_configuration(self) -> Tuple[bool, str]:
        """Validate security configuration"""
        # Check CDK stack has security features
        stack_file = self.project_root / "infrastructure/stacks/riskintel360_stack.py"
        with open(stack_file, 'r') as f:
            stack_content = f.read()
        
        security_features = [
            "kms.Key",
            "BucketEncryption.KMS",
            "TableEncryption.CUSTOMER_MANAGED",
            "SecurityGroup",
            "CloudTrail"
        ]
        
        missing_security = []
        for feature in security_features:
            if feature not in stack_content:
                missing_security.append(feature)
        
        if missing_security:
            return False, f"Missing security features: {', '.join(missing_security)}"
        
        # Check environment files don't have hardcoded secrets
        env_files = [".env.example", ".env.development"]
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                # Check for potential hardcoded secrets
                suspicious_patterns = ["password=", "secret=", "key="]
                for pattern in suspicious_patterns:
                    if pattern in env_content.lower() and "your-" not in env_content.lower():
                        self.warnings.append(f"Potential hardcoded secret in {env_file}")
        
        return True, "Security configuration valid"
    
    def _validate_performance_configuration(self) -> Tuple[bool, str]:
        """Validate performance configuration"""
        # Check CDK stack has auto-scaling
        stack_file = self.project_root / "infrastructure/stacks/riskintel360_stack.py"
        with open(stack_file, 'r') as f:
            stack_content = f.read()
        
        performance_features = [
            "auto_scale_task_count",
            "scale_on_cpu_utilization",
            "scale_on_memory_utilization",
            "HealthCheck",
            "CloudWatch"
        ]
        
        missing_performance = []
        for feature in performance_features:
            if feature not in stack_content:
                missing_performance.append(feature)
        
        if missing_performance:
            return False, f"Missing performance features: {', '.join(missing_performance)}"
        
        # Check docker-compose has health checks
        compose_file = self.project_root / "docker-compose.yml"
        with open(compose_file, 'r') as f:
            compose_content = f.read()
        
        if "healthcheck:" not in compose_content:
            return False, "Docker compose missing health checks"
        
        return True, "Performance configuration valid"
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📊 Validation Report Summary")
        print("=" * 50)
        
        total_validations = len(self.validation_results)
        passed_validations = sum(1 for result in self.validation_results.values() if result["success"])
        
        print(f"Total Validations: {total_validations}")
        print(f"Passed: {passed_validations}")
        print(f"Failed: {total_validations - passed_validations}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        # Overall status
        if passed_validations == total_validations and not self.errors:
            print("\n🎉 ALL VALIDATIONS PASSED - DEPLOYMENT READY!")
            print("\n📋 Next Steps:")
            print("   1. Run infrastructure deployment: ./scripts/deploy_infrastructure.sh development")
            print("   2. Run Docker deployment: ./scripts/deploy_docker.sh development dev")
            print("   3. Run infrastructure tests: python tests/run_infrastructure_tests.py")
            print("   4. Verify competition demo: python demo/run_demo.py")
        else:
            print("\n❌ Some validations failed - fix issues before deployment")
        
        # Save detailed report
        report = {
            "timestamp": time.time(),
            "summary": {
                "total_validations": total_validations,
                "passed": passed_validations,
                "failed": total_validations - passed_validations,
                "warnings_count": len(self.warnings),
                "errors_count": len(self.errors)
            },
            "results": self.validation_results,
            "warnings": self.warnings,
            "errors": self.errors,
            "deployment_ready": passed_validations == total_validations and not self.errors
        }
        
        report_file = self.project_root / "deployment_validation_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Main entry point"""
    print("RiskIntel360 Deployment Validation")
    print("=" * 40)
    
    validator = DeploymentValidator()
    success = validator.validate_all()
    
    if success:
        print("\n🎯 Deployment validation completed successfully!")
        print("✅ Ready for infrastructure deployment!")
        sys.exit(0)
    else:
        print("\n💥 Deployment validation failed!")
        print("❌ Fix issues before proceeding with deployment")
        sys.exit(1)


if __name__ == "__main__":
    main()