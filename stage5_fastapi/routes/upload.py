"""
Upload routes — exam containers, subject-papers under an exam, and
student submissions under a subject-paper.

Hierarchy: Exam (e.g. "Mid-Term 2026") -> Subject-Paper (e.g. Physics,
subject_code PHY101, its own question paper + answer key, graded by a
specific teacher) -> Submission (one student's answer sheet, tied to a
roll number and, if it matches an existing student account, a
student_id).
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from stage5_api.db.mongo import exams, subject_papers, submissions, users, results
from stage5_api.auth import require_role, get_current_user

exams_create_router = APIRouter(prefix="/exams", tags=["exams"])
subjects_router = APIRouter(prefix="/subjects", tags=["subjects"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_file(file: UploadFile, dest: str) -> str:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


@exams_create_router.post("")
async def create_exam(
    title: str = Form(...),
    term: str = Form(""),
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    """Create an exam container (e.g. 'Mid-Term 2026'). Subject-papers are added separately."""
    exam_id = str(uuid.uuid4())
    exam_doc = {
        "exam_id": exam_id,
        "title": title,
        "term": term,
        "created_by": current_user["user_id"],
        "created_at": datetime.utcnow().isoformat(),
        "status": "open",
    }
    exams().insert_one(exam_doc)
    return {"exam_id": exam_id, "title": title, "term": term, "message": "Exam created successfully"}


@exams_create_router.post("/{exam_id}/subjects")
async def create_subject_paper(
    exam_id: str,
    subject_name: str = Form(...),
    subject_code: str = Form(...),
    question_paper: UploadFile = File(...),
    answer_key: UploadFile = File(...),
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    """Add a subject's question paper + answer key under an exam. Grading of this subject is owned by the uploading teacher."""
    exam = exams().find_one({"exam_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam {exam_id} not found")

    subject_paper_id = str(uuid.uuid4())
    subject_dir = os.path.join(UPLOAD_DIR, "subjects", subject_paper_id)

    qp_path = save_file(question_paper, os.path.join(subject_dir, "question_paper.pdf"))
    ak_path = save_file(answer_key, os.path.join(subject_dir, "answer_key.pdf"))

    subject_doc = {
        "subject_paper_id": subject_paper_id,
        "exam_id": exam_id,
        "subject_name": subject_name,
        "subject_code": subject_code,
        "teacher_id": current_user["user_id"],
        "teacher_name": current_user["name"],
        "question_paper_path": qp_path,
        "answer_key_path": ak_path,
        "created_at": datetime.utcnow().isoformat(),
    }
    subject_papers().insert_one(subject_doc)

    return {
        "subject_paper_id": subject_paper_id,
        "exam_id": exam_id,
        "subject_name": subject_name,
        "subject_code": subject_code,
        "message": "Subject paper added successfully",
    }


@exams_create_router.get("/{exam_id}/subjects")
async def list_subject_papers(exam_id: str, current_user: dict = Depends(get_current_user)):
    """List subject-papers under an exam. Teachers only see their own; admin sees all."""
    all_subjects = subject_papers().find({"exam_id": exam_id})
    if current_user["role"] == "teacher":
        all_subjects = [s for s in all_subjects if s["teacher_id"] == current_user["user_id"]]
    for s in all_subjects:
        s.pop("_id", None)
    return all_subjects


@subjects_router.get("/{subject_paper_id}")
async def get_subject_paper(subject_paper_id: str, current_user: dict = Depends(get_current_user)):
    subject = subject_papers().find_one({"subject_paper_id": subject_paper_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject paper not found")
    if current_user["role"] == "teacher" and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only view subjects you teach")
    subject.pop("_id", None)
    return subject


@subjects_router.get("/{subject_paper_id}/submissions")
async def list_submissions(subject_paper_id: str, current_user: dict = Depends(get_current_user)):
    """List every submission (any status) for a subject-paper, with score if graded — the class roster view."""
    subject = subject_papers().find_one({"subject_paper_id": subject_paper_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject paper not found")
    if current_user["role"] == "teacher" and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only view submissions for subjects you teach")
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="Students cannot view class rosters")

    subs = submissions().find({"subject_paper_id": subject_paper_id})
    result_map = {r["submission_id"]: r for r in results().find({"subject_paper_id": subject_paper_id})}

    response = []
    for s in subs:
        s.pop("_id", None)
        r = result_map.get(s["submission_id"])
        s["score"] = r.get("total_scored") if r else None
        s["total_marks"] = r.get("total_marks") if r else None
        s["percentage"] = r.get("percentage") if r else None
        response.append(s)
    return response


@subjects_router.post("/{subject_paper_id}/submissions")
async def upload_submission(
    subject_paper_id: str,
    roll_no: str = Form(...),
    student_name: str = Form(...),
    student_answer: UploadFile = File(...),
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    """Upload one student's answer sheet for a subject-paper, keyed by roll number."""
    subject = subject_papers().find_one({"subject_paper_id": subject_paper_id})
    if not subject:
        raise HTTPException(status_code=404, detail=f"Subject paper {subject_paper_id} not found")

    if current_user["role"] == "teacher" and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only upload submissions for subjects you teach")

    # try to link this submission to an existing student account by roll number
    student_user = users().find_one({"role": "student", "roll_no": roll_no})

    submission_id = str(uuid.uuid4())
    submission_dir = os.path.join(UPLOAD_DIR, "submissions", submission_id)
    ans_path = save_file(student_answer, os.path.join(submission_dir, "student_answer.pdf"))

    submission_doc = {
        "submission_id": submission_id,
        "subject_paper_id": subject_paper_id,
        "exam_id": subject["exam_id"],
        "subject_code": subject["subject_code"],
        "subject_name": subject["subject_name"],
        "roll_no": roll_no,
        "student_name": student_name,
        "student_id": student_user["user_id"] if student_user else None,
        "student_answer_path": ans_path,
        "created_at": datetime.utcnow().isoformat(),
        "status": "uploaded",
    }
    submissions().insert_one(submission_doc)

    return {
        "submission_id": submission_id,
        "subject_paper_id": subject_paper_id,
        "roll_no": roll_no,
        "student_name": student_name,
        "message": "Submission uploaded successfully",
    }
