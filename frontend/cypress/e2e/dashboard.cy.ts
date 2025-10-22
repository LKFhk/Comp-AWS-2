describe('Dashboard E2E Tests', () => {
  beforeEach(() => {
    // Mock API responses
    cy.intercept('GET', '/api/v1/validations*', {
      fixture: 'validations.json'
    }).as('getValidations');
    
    cy.intercept('GET', '/api/v1/health', {
      statusCode: 200,
      body: { status: 'ok', timestamp: new Date().toISOString() }
    }).as('healthCheck');
    
    cy.visit('/');
  });

  it('loads dashboard successfully', () => {
    cy.contains('RiskIntel360 Platform').should('be.visible');
    cy.contains('Welcome back').should('be.visible');
    cy.wait('@getValidations');
  });

  it('displays navigation menu', () => {
    cy.get('[role="navigation"]').should('be.visible');
    cy.contains('Dashboard').should('be.visible');
    cy.contains('New Validation').should('be.visible');
    cy.contains('Results').should('be.visible');
  });

  it('shows recent validations', () => {
    cy.wait('@getValidations');
    cy.contains('Recent Validations').should('be.visible');
  });

  it('displays key metrics', () => {
    cy.contains('Total Validations').should('be.visible');
    cy.contains('Success Rate').should('be.visible');
    cy.contains('Average Time').should('be.visible');
  });

  it('navigates to new validation', () => {
    cy.contains('New Validation').click();
    cy.url().should('include', '/validation/new');
    cy.contains('Validation Wizard').should('be.visible');
  });

  it('is accessible', () => {
    cy.checkAccessibility();
  });

  it('is responsive on mobile', () => {
    cy.viewport('iphone-x');
    cy.contains('RiskIntel360').should('be.visible');
    
    // Check mobile menu
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible');
    cy.get('[data-testid="mobile-menu-button"]').click();
    cy.contains('Dashboard').should('be.visible');
  });

  it('handles loading states', () => {
    cy.intercept('GET', '/api/v1/validations*', {
      delay: 2000,
      fixture: 'validations.json'
    }).as('slowValidations');
    
    cy.visit('/');
    cy.get('[role="progressbar"]').should('be.visible');
    cy.wait('@slowValidations');
    cy.get('[role="progressbar"]').should('not.exist');
  });

  it('handles error states', () => {
    cy.intercept('GET', '/api/v1/validations*', {
      statusCode: 500,
      body: { error: 'Internal server error' }
    }).as('errorValidations');
    
    cy.visit('/');
    cy.wait('@errorValidations');
    cy.contains('Error loading validations').should('be.visible');
  });
});
