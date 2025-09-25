# Testing Guide for RetailXAI Dashboard

This guide covers all testing aspects of the RetailXAI Dashboard, including backend, frontend, and E2E tests.

## 🧪 Test Structure

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py          # Test configuration and fixtures
│   │   ├── test_auth.py         # Authentication tests
│   │   ├── test_drafts.py       # Draft API tests
│   │   └── test_rbac.py         # RBAC tests
│   └── pytest.ini              # Pytest configuration
├── frontend/
│   ├── tests/
│   │   ├── setup.ts             # Test setup
│   │   └── components/          # Component tests
│   └── jest.config.js           # Jest configuration
├── e2e/
│   ├── tests/
│   │   └── dashboard.spec.ts    # E2E tests
│   └── playwright.config.ts     # Playwright configuration
└── scripts/
    └── test.sh                  # Test runner script
```

## 🚀 Quick Start

### Run All Tests
```bash
./scripts/test.sh
```

### Run Specific Test Suites
```bash
# Backend only
./scripts/test.sh --backend-only

# Frontend only
./scripts/test.sh --frontend-only

# E2E only
./scripts/test.sh --e2e-only

# Include E2E tests
./scripts/test.sh --include-e2e
```

### Run with Verbose Output
```bash
./scripts/test.sh --verbose
```

## 🔧 Backend Tests

### Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_drafts.py

# Specific test
pytest tests/test_drafts.py::test_create_draft

# Verbose output
pytest -v
```

### Test Categories

#### Authentication Tests (`test_auth.py`)
- User registration
- Login/logout
- Token validation
- Password hashing
- User info retrieval

#### Draft API Tests (`test_drafts.py`)
- CRUD operations
- Pagination
- Search functionality
- Publishing
- Validation
- Error handling

#### RBAC Tests (`test_rbac.py`)
- Permission checking
- Role-based access
- Unauthorized access
- Token validation
- Role hierarchy

### Test Fixtures

The `conftest.py` file provides:
- `db_session`: Database session for tests
- `client`: HTTP client for API testing
- `test_user`: Editor user for testing
- `test_admin_user`: Admin user for testing
- `auth_headers`: Authentication headers
- `admin_auth_headers`: Admin authentication headers

### Database Testing

Tests use an in-memory SQLite database:
- Fast test execution
- Isolated test environment
- Automatic cleanup
- No external dependencies

## 🎨 Frontend Tests

### Setup
```bash
cd frontend
npm install
```

### Run Tests
```bash
# All tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# Specific test file
npm test -- tests/components/Dashboard.test.tsx
```

### Test Categories

#### Component Tests
- `Dashboard.test.tsx`: Main dashboard component
- `DraftCard.test.tsx`: Individual draft cards
- `DraftsList.test.tsx`: Draft list component
- `HealthCard.test.tsx`: Health monitoring
- `StatsCard.test.tsx`: Statistics display

#### Test Utilities
- Mock API responses
- User interaction simulation
- State management testing
- Error handling
- Responsive design

### Testing Library

Uses React Testing Library:
- User-centric testing
- Accessible queries
- Realistic interactions
- Component isolation

## 🌐 E2E Tests

### Setup
```bash
cd e2e
npm install
npx playwright install
```

### Run Tests
```bash
# All tests
npx playwright test

# Specific test
npx playwright test dashboard.spec.ts

# Headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

### Test Categories

#### Dashboard E2E Tests
- Page navigation
- Component rendering
- User interactions
- API integration
- Error handling
- Responsive design

### Browser Support
- Chromium
- Firefox
- WebKit (Safari)

### Test Environment
- Local development servers
- Mock API responses
- Isolated test data
- Automatic cleanup

## 📊 Coverage Reports

### Backend Coverage
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend Coverage
```bash
cd frontend
npm run test:coverage
open coverage/lcov-report/index.html
```

### Coverage Targets
- **Backend**: >90% line coverage
- **Frontend**: >80% line coverage
- **Critical paths**: 100% coverage

## 🔍 Test Data Management

### Backend Test Data
- In-memory database
- Fixture-based data
- Automatic cleanup
- Isolated test cases

### Frontend Test Data
- Mock API responses
- Component props
- User interactions
- State management

### E2E Test Data
- Mock server responses
- Test user accounts
- Sample content
- Cleanup procedures

## 🐛 Debugging Tests

### Backend Debugging
```bash
# Run with debugger
pytest --pdb

# Print output
pytest -s

# Stop on first failure
pytest -x
```

### Frontend Debugging
```bash
# Debug mode
npm test -- --debug

# Verbose output
npm test -- --verbose

# Update snapshots
npm test -- --updateSnapshot
```

### E2E Debugging
```bash
# Debug mode
npx playwright test --debug

# Trace viewer
npx playwright show-trace trace.zip

# Screenshots
npx playwright test --screenshot=on
```

## 🚨 Common Issues

### Backend Issues
1. **Database connection**: Ensure test database is properly configured
2. **Async tests**: Use `pytest-asyncio` for async test functions
3. **Fixtures**: Check fixture dependencies and scope
4. **Authentication**: Verify token generation and validation

### Frontend Issues
1. **Mock setup**: Ensure mocks are properly configured
2. **Async operations**: Use `waitFor` for async state changes
3. **Component rendering**: Check for missing dependencies
4. **API calls**: Verify mock responses match expected format

### E2E Issues
1. **Server startup**: Ensure both frontend and backend are running
2. **Timing**: Add appropriate waits for async operations
3. **Selectors**: Use stable, accessible selectors
4. **Data cleanup**: Ensure test data is properly cleaned up

## 📈 Performance Testing

### Backend Performance
```bash
# Load testing with pytest-benchmark
pytest --benchmark-only

# Memory profiling
pytest --profile
```

### Frontend Performance
```bash
# Bundle analysis
npm run build
npm run analyze

# Performance testing
npm run test:performance
```

## 🔄 Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Push to main branch
- Manual trigger

### Test Matrix
- Python 3.12
- Node.js 20
- Multiple browsers
- Different operating systems

## 📝 Writing New Tests

### Backend Test Template
```python
@pytest.mark.asyncio
async def test_new_feature(client: AsyncClient, auth_headers):
    """Test description."""
    response = await client.post(
        "/api/endpoint",
        json={"data": "value"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["field"] == "expected_value"
```

### Frontend Test Template
```typescript
describe('ComponentName', () => {
  it('should render correctly', () => {
    render(<ComponentName prop="value" />)
    
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### E2E Test Template
```typescript
test('should perform user action', async ({ page }) => {
  await page.goto('/')
  
  await page.click('button[data-testid="action-button"]')
  
  await expect(page.getByText('Success message')).toBeVisible()
})
```

## 🎯 Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't rely on external services
5. **Test Edge Cases**: Include error scenarios
6. **Keep Tests Fast**: Optimize for speed
7. **Maintain Test Data**: Keep test data up to date
8. **Document Complex Tests**: Add comments for clarity

---

**Happy Testing! 🧪✨**
