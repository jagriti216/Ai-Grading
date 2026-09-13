"""
FastAPI main entry point.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from stage5_api.routes.upload    import exams_create_router, subjects_router
from stage5_api.routes.grade     import router as grade_router
from stage5_api.routes.results   import router as results_router, exams_router
from stage5_api.routes.auth      import router as auth_router
from stage5_api.routes.admin     import router as admin_router
from stage5_api.routes.analytics import router as analytics_router
from stage5_api.db.mongo         import ping, seed_admin_if_missing, seed_demo_users_if_missing

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title       = "AI Grading System",
    description = "Automated grading system for handwritten and typed answer sheets",
    version     = "1.0.0"
)

# CORS — allow the configured frontend origin(s). Defaults to local dev origins.
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins     = cors_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(exams_create_router)
app.include_router(subjects_router)
app.include_router(grade_router)
app.include_router(results_router)
app.include_router(exams_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def startup():
    ping()
    seed_admin_if_missing()
    seed_demo_users_if_missing()
    logger.info("AI Grading System API started")


@app.get("/")
async def root():
    return {
        "message": "AI Grading System API",
        "version": "1.0.0",
        "endpoints": {
            "login":              "POST /auth/login",
            "create_user":        "POST /admin/users (admin only)",
            "create_exam":        "POST /exams",
            "add_subject_paper":  "POST /exams/{exam_id}/subjects",
            "upload_submission":  "POST /subjects/{subject_paper_id}/submissions",
            "grade":              "POST /grade/{submission_id}",
            "get_result":         "GET  /results/{submission_id}",
            "get_subject_results": "GET  /results/subject/{subject_paper_id}",
            "get_my_results":     "GET  /results/student/me",
            "check_status":       "GET  /results/submission/{submission_id}/status",
            "subject_analytics":  "GET  /analytics/{exam_id}/{subject_code}"
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
