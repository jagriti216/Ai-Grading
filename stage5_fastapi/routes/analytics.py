"""
Analytics route — given an exam_id and a subject_code, returns a full
performance breakdown for that subject: class stats, per-question
averages, score distribution buckets, and a roll-no-wise roster.
"""

from fastapi import APIRouter, HTTPException, Depends
from stage5_api.db.mongo import subject_papers, results
from stage5_api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

PASS_THRESHOLD = 0.4
DISTRIBUTION_BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100.01)]


@router.get("/{exam_id}/{subject_code}")
async def get_subject_analytics(exam_id: str, subject_code: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="Analytics is a teacher/admin tool")

    subject = subject_papers().find_one({"exam_id": exam_id, "subject_code": subject_code})
    if not subject:
        raise HTTPException(status_code=404, detail=f"No subject '{subject_code}' found under exam {exam_id}")

    if current_user["role"] == "teacher" and subject["teacher_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only view analytics for subjects you teach")

    subject_results = list(results().find({"subject_paper_id": subject["subject_paper_id"]}))
    for r in subject_results:
        r.pop("_id", None)

    if not subject_results:
        return {
            "exam_id": exam_id,
            "subject_code": subject_code,
            "subject_name": subject["subject_name"],
            "teacher_name": subject["teacher_name"],
            "total_students": 0,
            "message": "No graded submissions yet for this subject.",
        }

    scores = [r["total_scored"] for r in subject_results]
    total_marks = subject_results[0]["total_marks"]
    percentages = [r.get("percentage") or (r["total_scored"] / total_marks * 100 if total_marks else 0) for r in subject_results]

    pass_count = len([s for s in scores if total_marks and s >= total_marks * PASS_THRESHOLD])
    fail_count = len(scores) - pass_count

    # per-question averages
    question_totals, question_counts, question_max = {}, {}, {}
    for r in subject_results:
        for q in r.get("questions", []):
            qn = q.get("q_number")
            question_totals[qn] = question_totals.get(qn, 0) + (q.get("score") or 0)
            question_counts[qn] = question_counts.get(qn, 0) + 1
            question_max[qn] = q.get("max_marks", 1)

    per_question = [
        {
            "q_number": qn,
            "average_score": round(question_totals[qn] / question_counts[qn], 2),
            "max_marks": question_max[qn],
        }
        for qn in sorted(question_totals.keys(), key=lambda x: (len(str(x)), str(x)))
    ]

    # score distribution buckets (by percentage)
    distribution = []
    for low, high in DISTRIBUTION_BUCKETS:
        count = len([p for p in percentages if low <= p < high])
        distribution.append({"range": f"{low}-{int(min(high, 100))}%", "count": count})

    roster = sorted(
        [
            {
                "roll_no": r.get("roll_no"),
                "student_name": r.get("student_name"),
                "total_scored": r.get("total_scored"),
                "total_marks": r.get("total_marks"),
                "percentage": r.get("percentage"),
                "submission_id": r.get("submission_id"),
            }
            for r in subject_results
        ],
        key=lambda x: (x["roll_no"] is None, str(x["roll_no"])),
    )

    return {
        "exam_id": exam_id,
        "subject_code": subject_code,
        "subject_name": subject["subject_name"],
        "teacher_name": subject["teacher_name"],
        "total_students": len(subject_results),
        "total_marks": total_marks,
        "average_score": round(sum(scores) / len(scores), 1),
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "average_percent": round(sum(percentages) / len(percentages), 1),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": round(pass_count / len(scores) * 100, 1),
        "per_question_averages": per_question,
        "score_distribution": distribution,
        "roster": roster,
    }
