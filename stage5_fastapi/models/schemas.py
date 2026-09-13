"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ExamCreate(BaseModel):
    title:   str
    subject: str
    date:    Optional[str] = None


class ExamResponse(BaseModel):
    exam_id:          str
    title:            str
    subject:          str
    total_marks:      Optional[float] = None
    num_questions:    Optional[int]   = None
    created_at:       str


class SubmissionResponse(BaseModel):
    submission_id: str
    exam_id:       str
    student_name:  str
    status:        str
    created_at:    str


class GradeResponse(BaseModel):
    submission_id: str
    student_name:  str
    total_scored:  float
    total_marks:   float
    percentage:    float
    overall_remark: str
    graded_at:     str


class QuestionResult(BaseModel):
    q_number:        str
    question_text:   str
    student_answer:  str
    expected_answer: str
    score:           Optional[float]
    max_marks:       int
    feedback:        Optional[dict]
    breakdown:       Optional[dict]


class FullResultResponse(BaseModel):
    submission_id:    str
    student_name:     str
    total_scored:     float
    total_marks:      float
    percentage:       float
    overall_remark:   str
    questions:        List[QuestionResult]
    graded_at:        str
