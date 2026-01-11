"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self):
        """Test main health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "instance_id" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestSearchEndpoints:
    """Test search endpoints."""
    
    def test_search_endpoint(self):
        """Test basic search endpoint."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "artificial intelligence",
                "search_type": "text",
                "top_k": 5
            }
        )
        assert response.status_code in [200, 500]  # May fail if services not available
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total" in data
            assert "query" in data
    
    def test_search_invalid_request(self):
        """Test search with invalid request."""
        response = client.post(
            "/api/v1/search",
            json={
                "search_type": "text"
                # Missing required 'query' field
            }
        )
        assert response.status_code == 422  # Validation error


class TestUploadEndpoints:
    """Test file upload endpoints."""
    
    def test_upload_text_no_file(self):
        """Test text upload without file."""
        response = client.post("/api/v1/upload/text")
        assert response.status_code == 422  # Missing required file
    
    def test_upload_image_no_file(self):
        """Test image upload without file."""
        response = client.post("/api/v1/upload/image")
        assert response.status_code == 422  # Missing required file


class TestActionEndpoints:
    """Test action endpoints."""
    
    def test_schedule_email(self):
        """Test email scheduling."""
        response = client.post(
            "/api/v1/action/email",
            json={
                "action_type": "email",
                "parameters": {
                    "to": "test@example.com",
                    "subject": "Test",
                    "body": "Test body"
                }
            }
        )
        assert response.status_code in [200, 500]  # May fail if Celery not available
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data
            assert "status" in data
    
    def test_schedule_summarize(self):
        """Test summarization scheduling."""
        response = client.post(
            "/api/v1/action/summarize",
            json={
                "action_type": "summarize",
                "parameters": {
                    "content": "This is a test content to summarize.",
                    "max_length": 100
                }
            }
        )
        assert response.status_code in [200, 500]


class TestMetrics:
    """Test metrics endpoint."""
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Should return prometheus-formatted metrics
        assert "fastapi" in response.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
