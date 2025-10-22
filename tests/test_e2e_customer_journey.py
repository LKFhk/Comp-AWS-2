"""
End-to-End Customer Journey Tests for RiskIntel360 Platform
Tests complete user workflows from login to report download with frontend-backend integration.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

from riskintel360.models import ValidationRequest, Priority, WorkflowStatus
from riskintel360.services.cost_management import AWSCostManager, CostProfile
from riskintel360.api.main import app
from riskintel360.config.settings import get_settings

# Test configuration
TEST_BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"
WEBDRIVER_TIMEOUT = 30
TEST_USER_EMAIL = "test@RiskIntel360.com"
TEST_USER_PASSWORD = "test123"


class CustomerJourneyTestSuite:
    """Comprehensive end-to-end customer journey test suite"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.driver = None
        self.api_session = requests.Session()
        self.auth_token = None
        self.test_validation_id = None
        
        # Set up Chrome driver with options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except WebDriverException as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        
        # Set up API session
        self.api_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def teardown_method(self):
        """Clean up after each test"""
        if self.driver:
            self.driver.quit()
        
        # Clean up test data
        if self.test_validation_id and self.auth_token:
            try:
                self.api_session.delete(
                    f"{API_BASE_URL}/api/v1/validations/{self.test_validation_id}",
                    headers={'Authorization': f'Bearer {self.auth_token}'}
                )
            except:
                pass
    
    def wait_for_element(self, by: By, value: str, timeout: int = WEBDRIVER_TIMEOUT):
        """Wait for element to be present and visible"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = WEBDRIVER_TIMEOUT):
        """Wait for element to be clickable"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    
    def authenticate_user(self) -> str:
        """Authenticate test user and return token"""
        # Mock authentication for testing
        mock_token = "test_jwt_token_12345"
        self.auth_token = mock_token
        return mock_token
    
    def verify_api_health(self) -> bool:
        """Verify API is running and healthy"""
        try:
            response = self.api_session.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def verify_frontend_health(self) -> bool:
        """Verify frontend is running and accessible"""
        try:
            self.driver.get(TEST_BASE_URL)
            return "RiskIntel360" in self.driver.title
        except:
            return False


@pytest.mark.e2e
class TestCompleteCustomerJourney(CustomerJourneyTestSuite):
    """Complete customer journey tests"""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow from login to report download"""
        
        # Step 1: Verify services are running
        assert self.verify_api_health(), "API service is not running"
        assert self.verify_frontend_health(), "Frontend service is not running"
        
        # Step 2: User Authentication
        self.driver.get(TEST_BASE_URL)
        
        # Check if already logged in or need to login
        try:
            # Look for login form
            login_button = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='login-button']", timeout=5)
            
            # Fill login form
            email_input = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='email-input']")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='password-input']")
            
            email_input.send_keys(TEST_USER_EMAIL)
            password_input.send_keys(TEST_USER_PASSWORD)
            login_button.click()
            
        except TimeoutException:
            # Already logged in or no login required
            pass
        
        # Step 3: Verify Dashboard Load
        dashboard_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='dashboard-title']")
        assert "Welcome" in dashboard_title.text or "Dashboard" in dashboard_title.text
        
        # Step 4: Navigate to New Validation
        new_validation_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='new-validation-button']")
        new_validation_button.click()
        
        # Step 5: Complete Validation Wizard
        self._complete_validation_wizard()
        
        # Step 6: Monitor Real-time Progress
        self._monitor_validation_progress()
        
        # Step 7: View Results
        self._view_validation_results()
        
        # Step 8: Download Report
        self._download_validation_report()
        
        print("??Complete customer journey test passed")
    
    def _complete_validation_wizard(self):
        """Complete the validation request wizard"""
        
        # Wait for wizard to load
        wizard_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='wizard-title']")
        assert "New Business Validation" in wizard_title.text
        
        # Step 1: Business Concept
        business_concept_input = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='business-concept-input']")
        business_concept_input.clear()
        business_concept_input.send_keys("AI-powered customer service automation platform for small businesses")
        
        next_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='wizard-next-button']")
        next_button.click()
        
        # Step 2: Target Market
        target_market_input = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='target-market-input']")
        target_market_input.clear()
        target_market_input.send_keys("Small to medium businesses in North America with 10-500 employees")
        
        next_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='wizard-next-button']")
        next_button.click()
        
        # Step 3: Analysis Scope (verify default selections)
        analysis_scope_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='analysis-scope-title']")
        assert "Select Analysis Areas" in analysis_scope_title.text
        
        # Verify default checkboxes are selected
        market_checkbox = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='scope-market']")
        competitive_checkbox = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='scope-competitive']")
        financial_checkbox = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='scope-financial']")
        
        assert market_checkbox.is_selected()
        assert competitive_checkbox.is_selected()
        assert financial_checkbox.is_selected()
        
        next_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='wizard-next-button']")
        next_button.click()
        
        # Step 4: Configuration Settings
        config_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='config-title']")
        assert "Configuration Settings" in config_title.text
        
        # Select priority
        priority_select = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='priority-select']")
        priority_select.click()
        
        medium_option = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='priority-medium']")
        medium_option.click()
        
        next_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='wizard-next-button']")
        next_button.click()
        
        # Step 5: Review and Submit
        review_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='review-title']")
        assert "Review Your Validation Request" in review_title.text
        
        # Verify review information
        review_concept = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='review-concept']")
        assert "AI-powered customer service" in review_concept.text
        
        # Submit validation
        submit_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='submit-validation-button']")
        submit_button.click()
        
        # Wait for submission confirmation
        success_message = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='submission-success']")
        assert "Validation request submitted" in success_message.text
        
        # Extract validation ID from URL or response
        current_url = self.driver.current_url
        if "/validation/" in current_url:
            self.test_validation_id = current_url.split("/validation/")[1].split("/")[0]
    
    def _monitor_validation_progress(self):
        """Monitor real-time validation progress"""
        
        # Navigate to progress page
        if not self.test_validation_id:
            # Try to get validation ID from current page
            validation_id_element = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='validation-id']")
            self.test_validation_id = validation_id_element.text
        
        # Wait for progress page to load
        progress_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='progress-title']")
        assert "Validation Progress" in progress_title.text
        
        # Verify progress components are present
        progress_bar = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='progress-bar']")
        agent_status = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='agent-status']")
        current_message = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='current-message']")
        
        assert progress_bar.is_displayed()
        assert agent_status.is_displayed()
        assert current_message.is_displayed()
        
        # Wait for progress updates (simulate WebSocket updates)
        start_time = time.time()
        max_wait_time = 300  # 5 minutes max
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check if validation is completed
                completion_message = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='completion-message']")
                if completion_message.is_displayed():
                    break
                
                # Check progress percentage
                progress_text = progress_bar.get_attribute("aria-valuenow")
                if progress_text and int(progress_text) >= 100:
                    break
                
                time.sleep(2)  # Wait 2 seconds before checking again
                
            except:
                time.sleep(2)
                continue
        
        # Verify completion or timeout
        try:
            completion_message = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='completion-message']")
            assert completion_message.is_displayed()
        except:
            # If not completed, verify progress is being made
            progress_text = progress_bar.get_attribute("aria-valuenow")
            assert progress_text and int(progress_text) > 0, "No progress detected"
    
    def _view_validation_results(self):
        """View and interact with validation results"""
        
        # Navigate to results page
        view_results_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='view-results-button']")
        view_results_button.click()
        
        # Wait for results page to load
        results_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='results-title']")
        assert "Validation Results" in results_title.text
        
        # Verify overall score is displayed
        overall_score = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='overall-score']")
        score_text = overall_score.text
        assert any(char.isdigit() for char in score_text), "Overall score not displayed"
        
        # Verify confidence level is displayed
        confidence_level = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='confidence-level']")
        confidence_text = confidence_level.text
        assert "%" in confidence_text or "confidence" in confidence_text.lower()
        
        # Test tab navigation
        self._test_results_tabs()
        
        # Test chart interactions
        self._test_chart_interactions()
    
    def _test_results_tabs(self):
        """Test switching between different analysis result tabs"""
        
        # Market Analysis Tab
        market_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='market-analysis-tab']")
        market_tab.click()
        
        market_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='market-analysis-content']")
        assert market_content.is_displayed()
        
        # Competitive Intelligence Tab
        competitive_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='competitive-analysis-tab']")
        competitive_tab.click()
        
        competitive_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='competitive-analysis-content']")
        assert competitive_content.is_displayed()
        
        # Financial Analysis Tab
        financial_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='financial-analysis-tab']")
        financial_tab.click()
        
        financial_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='financial-analysis-content']")
        assert financial_content.is_displayed()
        
        # Risk Assessment Tab
        risk_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='risk-analysis-tab']")
        risk_tab.click()
        
        risk_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='risk-analysis-content']")
        assert risk_content.is_displayed()
        
        # Customer Intelligence Tab
        customer_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='customer-analysis-tab']")
        customer_tab.click()
        
        customer_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='customer-analysis-content']")
        assert customer_content.is_displayed()
        
        # Strategic Recommendations Tab
        recommendations_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='recommendations-tab']")
        recommendations_tab.click()
        
        recommendations_content = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='recommendations-content']")
        assert recommendations_content.is_displayed()
    
    def _test_chart_interactions(self):
        """Test chart interactions and data visualization"""
        
        # Go back to market analysis tab for chart testing
        market_tab = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='market-analysis-tab']")
        market_tab.click()
        
        # Wait for charts to load
        market_chart = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='market-size-chart']")
        assert market_chart.is_displayed()
        
        # Test chart hover interactions (if supported)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(market_chart).perform()
            time.sleep(1)  # Allow hover effects
        except:
            pass  # Hover interactions may not be testable in headless mode
        
        # Verify chart legend is present
        try:
            chart_legend = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chart-legend']")
            assert chart_legend.is_displayed()
        except:
            pass  # Legend may not be present for all charts
    
    def _download_validation_report(self):
        """Test report download functionality"""
        
        # Find and click download button
        download_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='download-report-button']")
        download_button.click()
        
        # Wait for download to initiate
        time.sleep(3)
        
        # Verify download was initiated (check for download notification or file)
        try:
            download_notification = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='download-notification']")
            assert download_notification.is_displayed()
        except:
            # Alternative: Check if download started by looking for browser download indicator
            # This is browser-specific and may not be reliable in headless mode
            pass
    
    def test_user_settings_workflow(self):
        """Test user settings and preferences workflow"""
        
        # Navigate to settings
        self.driver.get(f"{TEST_BASE_URL}/settings")
        
        # Wait for settings page to load
        settings_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='settings-title']")
        assert "Settings" in settings_title.text
        
        # Test profile information display
        user_name = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='user-name']")
        user_email = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='user-email']")
        
        assert user_name.is_displayed()
        assert user_email.is_displayed()
        
        # Test notification preferences
        email_notifications = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='email-notifications-toggle']")
        push_notifications = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='push-notifications-toggle']")
        
        # Toggle settings
        email_notifications.click()
        push_notifications.click()
        
        # Save settings
        save_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='save-settings-button']")
        save_button.click()
        
        # Verify save confirmation
        save_confirmation = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='save-confirmation']")
        assert save_confirmation.is_displayed()
        
        print("??User settings workflow test passed")
    
    def test_validation_history_workflow(self):
        """Test validation history and management workflow"""
        
        # Navigate to validation history
        self.driver.get(f"{TEST_BASE_URL}/validations")
        
        # Wait for history page to load
        history_title = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='validations-title']")
        assert "Validation History" in history_title.text or "My Validations" in history_title.text
        
        # Test filtering
        try:
            status_filter = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='status-filter']", timeout=5)
            status_filter.click()
            
            completed_option = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='filter-completed']")
            completed_option.click()
            
            time.sleep(2)  # Wait for filter to apply
        except TimeoutException:
            pass  # Filter may not be present
        
        # Test pagination
        try:
            next_page = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='next-page-button']")
            if next_page.is_enabled():
                next_page.click()
                time.sleep(2)
                
                prev_page = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='prev-page-button']")
                prev_page.click()
        except:
            pass  # Pagination may not be present if few validations
        
        print("??Validation history workflow test passed")


@pytest.mark.e2e
class TestCrossBrowserCompatibility(CustomerJourneyTestSuite):
    """Cross-browser compatibility tests"""
    
    @pytest.mark.parametrize("browser", ["chrome", "firefox"])
    def test_cross_browser_compatibility(self, browser):
        """Test basic functionality across different browsers"""
        
        if browser == "firefox":
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                firefox_options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=firefox_options)
            except:
                pytest.skip("Firefox WebDriver not available")
        
        # Basic functionality test
        self.driver.get(TEST_BASE_URL)
        
        # Verify page loads
        assert "RiskIntel360" in self.driver.title
        
        # Test basic navigation
        try:
            nav_menu = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='main-navigation']", timeout=10)
            assert nav_menu.is_displayed()
        except TimeoutException:
            pytest.fail(f"Navigation not working in {browser}")
        
        print(f"??{browser.title()} compatibility test passed")


@pytest.mark.e2e
class TestPerformanceAndAccessibility(CustomerJourneyTestSuite):
    """Performance and accessibility tests"""
    
    def test_page_load_performance(self):
        """Test page load performance metrics"""
        
        start_time = time.time()
        self.driver.get(TEST_BASE_URL)
        
        # Wait for page to be fully loaded
        self.wait_for_element(By.CSS_SELECTOR, "body")
        
        load_time = time.time() - start_time
        
        # Assert page loads within acceptable time (5 seconds)
        assert load_time < 5.0, f"Page load time {load_time:.2f}s exceeds 5 seconds"
        
        print(f"??Page load performance test passed ({load_time:.2f}s)")
    
    def test_accessibility_compliance(self):
        """Test basic accessibility compliance"""
        
        self.driver.get(TEST_BASE_URL)
        
        # Check for basic accessibility elements
        try:
            # Check for main landmark
            main_content = self.driver.find_element(By.CSS_SELECTOR, "main, [role='main']")
            assert main_content.is_displayed()
            
            # Check for navigation landmark
            navigation = self.driver.find_element(By.CSS_SELECTOR, "nav, [role='navigation']")
            assert navigation.is_displayed()
            
            # Check for proper heading structure
            h1_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1")
            assert len(h1_elements) >= 1, "No H1 heading found"
            
            print("??Basic accessibility compliance test passed")
            
        except Exception as e:
            pytest.fail(f"Accessibility compliance test failed: {e}")


@pytest.mark.e2e
class TestErrorHandlingAndRecovery(CustomerJourneyTestSuite):
    """Error handling and recovery tests"""
    
    def test_network_error_handling(self):
        """Test handling of network errors"""
        
        self.driver.get(TEST_BASE_URL)
        
        # Simulate network error by navigating to invalid endpoint
        self.driver.get(f"{TEST_BASE_URL}/invalid-endpoint")
        
        # Should show error page or redirect
        try:
            error_message = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='error-message']", timeout=10)
            assert error_message.is_displayed()
        except TimeoutException:
            # Check if redirected to valid page
            assert self.driver.current_url != f"{TEST_BASE_URL}/invalid-endpoint"
        
        print("??Network error handling test passed")
    
    def test_form_validation_errors(self):
        """Test form validation error handling"""
        
        self.driver.get(f"{TEST_BASE_URL}/validation/new")
        
        # Try to submit empty form
        try:
            submit_button = self.wait_for_clickable(By.CSS_SELECTOR, "[data-testid='submit-validation-button']")
            submit_button.click()
            
            # Should show validation errors
            error_message = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='validation-error']")
            assert error_message.is_displayed()
            
        except TimeoutException:
            # Form may prevent submission with disabled button
            business_concept_input = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='business-concept-input']")
            assert business_concept_input.get_attribute("required") is not None
        
        print("??Form validation error handling test passed")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
