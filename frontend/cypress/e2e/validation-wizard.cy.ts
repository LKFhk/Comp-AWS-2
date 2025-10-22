describe('Validation Wizard E2E Tests', () => {
  beforeEach(() => {
    // Mock API responses
    cy.intercept('POST', '/api/v1/validations', {
      statusCode: 201,
      body: {
        id: 'test-validation-123',
        status: 'processing',
        created_at: new Date().toISOString()
      }
    }).as('createValidation');
    
    cy.visit('/validation/new');
  });

  it('displays validation wizard form', () => {
    cy.contains('Validation Wizard').should('be.visible');
    cy.contains('Business Concept').should('be.visible');
    cy.contains('Target Market').should('be.visible');
  });

  it('validates required fields', () => {
    cy.get('[data-testid="submit-button"]').click();
    cy.contains('Business concept is required').should('be.visible');
    cy.contains('Target market is required').should('be.visible');
  });

  it('completes validation request successfully', () => {
    // Fill out the form
    cy.get('[data-testid="business-concept-input"]')
      .type('AI-powered project management tool for remote teams');
    
    cy.get('[data-testid="target-market-input"]')
      .type('Small to medium businesses with remote teams');
    
    cy.get('[data-testid="industry-select"]').click();
    cy.contains('Technology').click();
    
    cy.get('[data-testid="priority-select"]').click();
    cy.contains('High').click();
    
    // Submit the form
    cy.get('[data-testid="submit-button"]').click();
    
    cy.wait('@createValidation');
    
    // Should redirect to progress page
    cy.url().should('include', '/validation/test-validation-123');
    cy.contains('Validation in Progress').should('be.visible');
  });

  it('shows form validation errors', () => {
    cy.get('[data-testid="business-concept-input"]').type('a');
    cy.get('[data-testid="business-concept-input"]').clear();
    cy.get('[data-testid="target-market-input"]').click();
    
    cy.contains('Business concept is required').should('be.visible');
  });

  it('supports step-by-step navigation', () => {
    // Step 1: Basic Information
    cy.contains('Step 1').should('be.visible');
    cy.get('[data-testid="business-concept-input"]')
      .type('AI-powered project management tool');
    
    cy.get('[data-testid="next-button"]').click();
    
    // Step 2: Market Details
    cy.contains('Step 2').should('be.visible');
    cy.get('[data-testid="target-market-input"]')
      .type('Small businesses');
    
    cy.get('[data-testid="next-button"]').click();
    
    // Step 3: Analysis Scope
    cy.contains('Step 3').should('be.visible');
    cy.get('[data-testid="market-analysis-checkbox"]').check();
    cy.get('[data-testid="competitive-analysis-checkbox"]').check();
    
    cy.get('[data-testid="next-button"]').click();
    
    // Step 4: Review and Submit
    cy.contains('Step 4').should('be.visible');
    cy.contains('Review Your Request').should('be.visible');
  });

  it('allows going back to previous steps', () => {
    // Navigate to step 2
    cy.get('[data-testid="business-concept-input"]')
      .type('Test concept');
    cy.get('[data-testid="next-button"]').click();
    
    // Go back to step 1
    cy.get('[data-testid="back-button"]').click();
    cy.contains('Step 1').should('be.visible');
    cy.get('[data-testid="business-concept-input"]')
      .should('have.value', 'Test concept');
  });

  it('saves draft automatically', () => {
    cy.get('[data-testid="business-concept-input"]')
      .type('Draft concept');
    
    // Wait for auto-save
    cy.wait(2000);
    
    // Refresh page
    cy.reload();
    
    // Check if draft is restored
    cy.get('[data-testid="business-concept-input"]')
      .should('have.value', 'Draft concept');
  });

  it('is accessible', () => {
    cy.checkAccessibility();
  });

  it('handles API errors gracefully', () => {
    cy.intercept('POST', '/api/v1/validations', {
      statusCode: 400,
      body: { error: 'Invalid request data' }
    }).as('errorValidation');
    
    cy.get('[data-testid="business-concept-input"]')
      .type('Test concept');
    cy.get('[data-testid="target-market-input"]')
      .type('Test market');
    
    cy.get('[data-testid="submit-button"]').click();
    
    cy.wait('@errorValidation');
    cy.contains('Error creating validation').should('be.visible');
  });
});