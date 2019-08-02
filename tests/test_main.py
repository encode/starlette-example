from starlette.responses import HTMLResponse
from starlette.testclient import TestClient
import pytest

from app.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'mi porta gravida at' in response.content.decode('utf-8')

def test_missing(client):
    response = client.get('/fake-path')
    assert response.status_code == 404
    assert 'Page not found.' in response.content.decode('utf-8')

