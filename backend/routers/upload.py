"""
Upload Router — Handles PDF file uploads and storage.

Files are stored in Supabase Storage bucket 'exam-papers'.
Path format: {user_id}/{subject_id}/{filename}
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(tags=["Upload"])

# Constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
]


@router.post("/upload")
async def upload_exam_paper(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    subject_name: str = Form(""),
    year: int = Form(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload a PDF exam paper.

    - If subject_id is "new", creates a new subject with subject_name.
    - Stores PDF in Supabase Storage.
    - Creates upload record in DB.
    """
    # === File Validation ===

    # Check file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only PDF files are accepted.",
        )

    # Check filename extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a .pdf extension.",
        )

    # Read file and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is 20MB, got {len(file_bytes) / (1024*1024):.1f}MB.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty.",
        )

    try:
        supabase = get_supabase()

        # === Handle Subject ===
        actual_subject_id = subject_id

        if subject_id == "new":
            if not subject_name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject name is required when creating a new subject.",
                )

            # Create new subject
            subject_result = (
                supabase.table("subjects")
                .insert({"user_id": user["id"], "name": subject_name.strip()})
                .execute()
            )

            if not subject_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create subject.",
                )

            actual_subject_id = subject_result.data[0]["id"]
        else:
            # Verify subject exists and belongs to user
            check = (
                supabase.table("subjects")
                .select("id")
                .eq("id", subject_id)
                .eq("user_id", user["id"])
                .execute()
            )
            if not check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found.",
                )

        # === Upload to Supabase Storage ===

        # Generate unique filename to avoid collisions
        safe_filename = file.filename.replace(" ", "_")
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
        storage_path = f"{user['id']}/{actual_subject_id}/{unique_name}"

        # Upload file to storage bucket
        storage_response = supabase.storage.from_("exam-papers").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},
        )

        # === Create Upload Record ===
        upload_result = (
            supabase.table("uploads")
            .insert({
                "subject_id": actual_subject_id,
                "user_id": user["id"],
                "file_path": storage_path,
                "year": year,
                "filename": file.filename,
                "status": "pending",
            })
            .execute()
        )

        if not upload_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save upload record.",
            )

        upload = upload_result.data[0]

        return {
            "upload_id": upload["id"],
            "subject_id": actual_subject_id,
            "file_path": storage_path,
            "filename": file.filename,
            "year": year,
            "status": "uploaded",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/uploads/{subject_id}")
async def list_uploads(
    subject_id: str,
    user: dict = Depends(get_current_user),
):
    """List all uploads for a subject."""
    try:
        supabase = get_supabase()

        # Verify subject ownership
        check = (
            supabase.table("subjects")
            .select("id")
            .eq("id", subject_id)
            .eq("user_id", user["id"])
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found.",
            )

        result = (
            supabase.table("uploads")
            .select("id, filename, year, status, created_at")
            .eq("subject_id", subject_id)
            .order("year", desc=True)
            .execute()
        )

        return {"uploads": result.data or []}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list uploads: {str(e)}",
        )
