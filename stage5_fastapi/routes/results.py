"""
Results routes — fetch grading results, scoped by role:
  - student: only their own results (matched by student_id or roll_no)
  - teacher: only results for subject-papers they teach
  - admin:   everything
"""

from fastapi import APIRouter, HTTPException, Depends
from stage5_api.db.mongo import exams, subject_papers, submissions, results, users
from stage5_api.auth import get_current_user

router = APIRouter(prefix="/results", tags=["results"])


def _can_view_result(result: dict, current_user: dict) -> bool:
    if current_user["role"] == "admin":
        return True
    if current_user["role"] == "teacher":
        return result.get("teacher_id") == current_user["user_id"]
    if current_user["role"] == "student":
        if result.get("student_id") and result["student_id"] == current_user["user_id"]:
            return True
        # fall back to matching by roll_no if the account's roll_no matches
        user = users().find_one({"user_id": current_user["user_id"]})
        return bool(user and user.get("roll_no") and user["roll_no"] == result.get("roll_no"))
    return False


@router.get("/{submission_id}")
async def get_result(submission_id: str, current_user: dict = Depends(get_current_user)):
    """Get full grading result for a submission."""
    submission = submissions().find_one({"submission_id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission["status"] == "grading":
        return {"status": "grading", "message": "Still processing, check back soon"}

    if submission["status"] == "failed":
        return {"status": "failed", "error": submission.get("error", "Unknown error")}

    if submission["status"] == "uploaded":
        return {"status": "uploaded", "message": "Grading not started yet"}

    result = results().find_one({"submission_id": submission_id})
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    if not _can_view_result(result, current_user):
        raise HTTPException(status_code=403, detail="You don't have access to this result")

    result.pop("_id", None)
    return result


@router.get("/subject/{subject_paper_id}")
async def get_subject_results(subject_paper_id: str, current_user: dict = Depends(get_current_user)):
    """Class roster view: every graded submission for one subject-paper."""
    subject = subject_papers().find_one({"subject_paper_id": subject_paper_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject paper not found")

    if current_user["role"] == "teacher" and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only view results for subjects you teach")
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="Students cannot view class rosters")

    subject_results = list(results().find({"subject_paper_id": subject_paper_id}))
    for r in subject_results:
        r.pop("_id", None)
        r.pop("questions", None)
    return {
        "subject_paper_id": subject_paper_id,
        "subject_name": subject["subject_name"],
        "subject_code": subject["subject_code"],
        "exam_id": subject["exam_id"],
        "results": subject_results,
    }


@router.get("/student/me")
async def get_my_results(current_user: dict = Depends(get_current_user)):
    """A student's own results across every subject/exam they've been graded in."""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal results view")

    user = users().find_one({"user_id": current_user["user_id"]})
    query = {"student_id": current_user["user_id"]}
    my_results = list(results().find(query))

    # also catch results linked only by roll_no (e.g. submission uploaded before this account existed)
    if user and user.get("roll_no"):
        by_roll = list(results().find({"roll_no": user["roll_no"]}))
        seen_ids = {r["submission_id"] for r in my_results}
        my_results += [r for r in by_roll if r["submission_id"] not in seen_ids]

    for r in my_results:
        r.pop("_id", None)
    return my_results


@router.get("/submission/{submission_id}/status")
async def get_status(submission_id: str, current_user: dict = Depends(get_current_user)):
    """Quick status check for a submission."""
    submission = submissions().find_one({"submission_id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {
        "submission_id": submission_id,
        "status":        submission["status"]
    }


exams_router = APIRouter(prefix="/exams", tags=["exams"])


@exams_router.get("")
async def list_exams(current_user: dict = Depends(get_current_user)):
    """List all exam containers (title/term only — subject/result detail is separately scoped)."""
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="Students should use /results/student/me")
    all_exams = list(exams().find({}))
    for exam in all_exams:
        exam.pop("_id", None)
        subs = subject_papers().find({"exam_id": exam["exam_id"]})
        if current_user["role"] == "teacher":
            subs = [s for s in subs if s["teacher_id"] == current_user["user_id"]]
        exam["subject_count"] = len(subs)
    return all_exams


@exams_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Overall dashboard metrics, scoped to the teacher's own subjects unless admin."""
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="Not available for student accounts")

    all_results = list(results().find({}))
    if current_user["role"] == "teacher":
        all_results = [r for r in all_results if r.get("teacher_id") == current_user["user_id"]]

    total_exams = len(list(exams().find({})))
    total_graded = len(all_results)

    percents = [r["percentage"] for r in all_results if r.get("percentage") is not None]
    avg_score = round(sum(percents) / len(percents), 1) if percents else 0.0

    sorted_results = sorted(all_results, key=lambda x: x.get("graded_at", ""), reverse=True)
    recent_submissions = []
    for r in sorted_results[:5]:
        exam = exams().find_one({"exam_id": r.get("exam_id")})
        recent_submissions.append({
            "submission_id": r.get("submission_id"),
            "student_name": r.get("student_name"),
            "roll_no": r.get("roll_no"),
            "subject_name": r.get("subject_name"),
            "exam_id": r.get("exam_id"),
            "exam_title": exam.get("title") if exam else "Unknown Exam",
            "total_scored": r.get("total_scored"),
            "total_marks": r.get("total_marks"),
            "percentage": r.get("percentage"),
            "graded_at": r.get("graded_at")
        })

    return {
        "total_exams": total_exams,
        "total_graded_submissions": total_graded,
        "average_percentage": avg_score,
        "recent_activity": recent_submissions
    }


@exams_router.get("/{exam_id}")
async def get_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    """Get single exam details with its subject-papers (scoped to teacher's own)."""
    exam = exams().find_one({"exam_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.pop("_id", None)

    subs = subject_papers().find({"exam_id": exam_id})
    if current_user["role"] == "teacher":
        subs = [s for s in subs if s["teacher_id"] == current_user["user_id"]]
    for s in subs:
        s.pop("_id", None)
    exam["subjects"] = subs
    return exam


@exams_router.delete("/{exam_id}")
async def delete_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an exam and everything under it. Admin only."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete exams")

    exam = exams().find_one({"exam_id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    subject_ids = [s["subject_paper_id"] for s in subject_papers().find({"exam_id": exam_id})]

    exams().delete_one({"exam_id": exam_id})
    subject_papers().delete_many({"exam_id": exam_id})
    for sid in subject_ids:
        submissions().delete_many({"subject_paper_id": sid})
        results().delete_many({"subject_paper_id": sid})

    return {"message": "Exam and all associated subjects, submissions and results deleted successfully"}
