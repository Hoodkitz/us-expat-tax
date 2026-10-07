"""
Shared test configuration for all backend tests.
"""
import pytest
from app.main import app
from app.auth.utils import get_current_tenant


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Override get_current_tenant for all tests to avoid 401 errors."""
    
    async def mock_get_current_tenant():
        """Return a mock tenant dict for testing."""
        return {
            "tenant_id": "test-tenant-123",
            "email": "test@example.com",
            "tenant_name": "Test Tenant",
        }
    
    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant
    yield
    app.dependency_overrides.clear()
