import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales_orders", tags=["sales_orders"])


@router.get("/")
@login_required
def get_sales_orders(request: Request, response: Response, db: Session = Depends(get_db)):
    """Get all sales orders"""
    logs = GenerationLogs.pull_so_logs(db)
    return {
        "message": "Sales orders retrieved successfully",
        "sales_orders": logs
    }
