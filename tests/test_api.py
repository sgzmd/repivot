import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.auth import require_auth
import io
import pandas as pd
import os
import uuid
from unittest.mock import patch

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # Use file db to avoid in-memory thread issues
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Reset DB
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock auth
async def override_require_auth():
    return {"email": "test@example.com", "name": "Test User"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[require_auth] = override_require_auth

client = TestClient(app)

def create_sample_xls_bytes():
    data = {
        'Type': ['Card Payment'],
        'Product': ['Current'],
        'Completed Date': ['2023-01-01 10:00:00'],
        'Description': ['Test Expense'],
        'Amount': [10.00],
        'Fee': [0.00],
        'Currency': ['GBP']
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def teardown_module(module):
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    if os.path.exists("./temp_uploads"):
        import shutil
        shutil.rmtree("./temp_uploads")

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Upload Expenses" in response.text
    assert "test@example.com" in response.text

def test_upload_flow():
    xls_content = create_sample_xls_bytes()
    files = {'file': ('test.xls', xls_content, 'application/vnd.ms-excel')}
    
    response = client.post(
        "/upload",
        files=files,
        data={"person": "Eva"}
    )
    if "Error processing file" in response.text:
        print(response.text)
        
    assert response.status_code == 200
    assert "Successfully processed 1 records" in response.text

def test_share_target_flow():
    xls_content = create_sample_xls_bytes()
    files = {'file': ('share.xls', xls_content, 'application/vnd.ms-excel')}
    
    # 1. Share (no person)
    # We mock uuid to be deterministic
    known_uuid = "1234-5678"
    
    with patch("uuid.uuid4", return_value=known_uuid):
        response = client.post(
            "/upload",
            files=files
        )
            
    assert response.status_code == 200
    assert "Finalize Upload" in response.text
    
    # Check if file exists
    temp_path = f"temp_uploads/{known_uuid}.xls"
    assert os.path.exists(temp_path)
    
    # 2. Finalize
    response = client.post(
        "/upload/finalize",
        data={"file_id": known_uuid, "person": "Sophie"}
    )
    assert response.status_code == 200
    assert "Successfully processed 1 records for Sophie" in response.text
    
    # File should be gone
    assert not os.path.exists(temp_path)

def test_report_population():
    # View Report
    response = client.get("/reports")
    assert response.status_code == 200
    # Data from previous tests should be there if we use persistent DB file
    # "Eva" from test_upload_flow, "Sophie" from test_share_target_flow
    assert "Eva" in response.text
    assert "Sophie" in response.text
