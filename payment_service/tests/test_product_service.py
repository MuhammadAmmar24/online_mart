from fastapi.testclient import TestClient
from fastapi import FastAPI
from app import setting
from sqlmodel import SQLModel, create_engine, Sequence
from app.main import app
from app.deps import get_session
import pytest 


# TEST 1: root test
def test_root():
    client = TestClient(app=app)
    response = client.get('/')
    data = response.json()
    assert response.status_code == 200
    assert data = {"message": "Product Service"}


