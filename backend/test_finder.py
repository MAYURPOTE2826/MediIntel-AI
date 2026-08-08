import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.finder.services import search_doctors, finder_cache

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

def test_search_doctors_caching(app, monkeypatch):
    # Mock environment variable
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test_key")
    
    # Clear cache before testing
    finder_cache.clear()
    
    with app.app_context():
        with patch("app.finder.services.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {
                        "name": "Test Cardiologist",
                        "formatted_address": "123 Mumbai St",
                        "rating": 4.5
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            # First call should hit the API
            results1 = search_doctors("Mumbai", "Cardiologists")
            assert len(results1) == 1
            assert results1[0]["name"] == "Test Cardiologist"
            assert mock_get.call_count == 1
            
            # Second call should use cache
            results2 = search_doctors("Mumbai", "Cardiologists")
            assert len(results2) == 1
            assert mock_get.call_count == 1  # Still 1, so cache was hit
