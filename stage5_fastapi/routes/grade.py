"""
Grading route — triggers full pipeline for a submission.
"""

import logging
import os
import shutil
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from stage5_api.db.mongo import subject_papers, submissions, results
from stage5_api.pipeline.runner import run_pipeline
from stage5_api.auth import require_role, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/grade", tags=["grade"])


def run_grading_job(submission_id: str):
    """Background task that runs the full pipeline."""
    submission = submissions().find_one({"submission_id": submission_id})
    if not submission:
        return
    subject = subject_papers().find_one({"subject_paper_id": submission["subject_paper_id"]})
    if not subject:
        return

    submissions().update_one(
        {"submission_id": submission_id},
        {"$set": {"status": "grading"}}
    )

    try:
        output_dir = os.path.join("outputs", submission_id)

        result = run_pipeline(
            question_paper_path=subject["question_paper_path"],
            answer_key_path=subject["answer_key_path"],
            student_answer_path=submission["student_answer_path"],
            output_dir=output_dir
        )

        result_doc = {
            "submission_id":  submission_id,
            "subject_paper_id": submission["subject_paper_id"],
            "exam_id":        submission["exam_id"],
            "subject_code":   submission["subject_code"],
            "subject_name":   submission["subject_name"],
            "teacher_id":     subject["teacher_id"],
            "roll_no":        submission["roll_no"],
            "student_id":     submission.get("student_id"),
            "student_name":   result.get("student_name") or submission["student_name"],
            "total_scored":   result["total_scored"],
            "total_marks":    result["total_marks"],
            "percentage":     result.get("percentage", 0),
            "overall_remark": result.get("feedback_summary", {}).get("overall_remark", ""),
            "questions":      result["questions"],
            "graded_at":      datetime.utcnow().isoformat()
        }

        results().insert_one(result_doc)

        submissions().update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "graded"}}
        )

        # The result is now durably stored (Mongo/local-JSON) — the local
        # intermediate stage files (extraction/parsing/grading JSON) were
        # only ever needed for debugging this run, so clear them
        # immediately instead of letting outputs/ grow unbounded forever.
        shutil.rmtree(output_dir, ignore_errors=True)

    except Exception as e:
        # On failure, deliberately keep output_dir — whatever intermediate
        # files exist are the only trace of what went wrong, and deleting
        # them here would make the failure undebuggable.
        submissions().update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        logger.exception("Grading failed for %s", submission_id)


@router.post("/{submission_id}")
async def grade_submission(
    submission_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin", "teacher")),
):
    """
    Triggers grading pipeline for a submission.
    Runs in background — check /results/{submission_id} for output.
    """
    submission = submissions().find_one({"submission_id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    subject = subject_papers().find_one({"subject_paper_id": submission["subject_paper_id"]})
    if current_user["role"] == "teacher" and subject and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only grade submissions for subjects you teach")

    if submission["status"] == "grading":
        return {"message": "Grading already in progress", "submission_id": submission_id}

    if submission["status"] == "graded":
        return {"message": "Already graded", "submission_id": submission_id}

    background_tasks.add_task(run_grading_job, submission_id)

    return {
        "message":       "Grading started",
        "submission_id": submission_id,
        "status":        "grading"
    }
