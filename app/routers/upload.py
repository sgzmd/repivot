from fastapi import APIRouter, UploadFile, File, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from sqlalchemy.orm import Session
from ..processor import process_revolut_file
from ..database import get_db
from ..auth import require_auth
from ..dependencies import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: dict = Depends(require_auth)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

import shutil
import uuid
import os

@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    person: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    if person is None:
        # Share Target flow: stash file and ask for person
        file_id = str(uuid.uuid4())
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{file_id}.xls")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return templates.TemplateResponse("select_person.html", {
            "request": request,
            "user": user,
            "file_id": file_id,
            "filename": file.filename
        })

    try:
        content = await file.read()
        count = process_revolut_file(content, person, db)
        message = f"Successfully processed {count} records for {person}."
        msg_type = "success"
    except Exception as e:
        message = f"Error processing file: {str(e)}"
        msg_type = "error"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "message": message,
        "msg_type": msg_type
    })

@router.post("/upload/finalize", response_class=HTMLResponse)
async def finalize_upload(
    request: Request,
    file_id: str = Form(...),
    person: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    temp_dir = "temp_uploads"
    file_path = os.path.join(temp_dir, f"{file_id}.xls")
    
    if not os.path.exists(file_path):
         return templates.TemplateResponse("index.html", {
            "request": request,
            "user": user,
            "message": "File processing session expired or invalid.",
            "msg_type": "error"
        })
        
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        count = process_revolut_file(content, person, db)
        message = f"Successfully processed {count} records for {person}."
        msg_type = "success"
        
        # Cleanup
        os.remove(file_path)
        
    except Exception as e:
        message = f"Error processing file: {str(e)}"
        msg_type = "error"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "message": message,
        "msg_type": msg_type
    })
