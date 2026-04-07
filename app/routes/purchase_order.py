import logging
import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderCreate

from app.helper.file_helper import generate_tsv_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sales_orders", tags=["sales_orders"])