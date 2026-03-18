from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, UUID, DateTime, ForeignKey, Integer, String

from app.database import get_db, Base, gen_uuid

db = get_db()

class GenerationLogs(Base):
    __tablename__ = "generation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, index=True)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    generated_file_type = Column(String(30), nullable=False)
    success_flag = Column(Boolean, default=False)
    total_records_generated = Column(Integer, default=0)
    successful_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    validated_records_count = Column(Integer, default=0)
    successful_generated_ids = Column(JSON, nullable=True)  # List of generated successful file IDs
    generation_date = Column(DateTime, server_default=datetime.now(timezone.utc).isoformat())

    @staticmethod
    def log_generation(db, client_id: str, user_id: str, generated_file_type: str, success_flag: bool):
        """Log a new generation event to the database"""
        new_log = GenerationLogs(
            id=gen_uuid(),
            client_id=client_id,
            user_id=user_id,
            generated_file_type=generated_file_type,
            success_flag=success_flag
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    
    @staticmethod
    def update_generation_log(db, log_id: str, total_records_generated: int, successful_count: int, failed_count: int, validated_records_count: int, successful_generated_ids: list):
        """Update an existing generation log with results"""
        log_entry = db.query(GenerationLogs).filter(GenerationLogs.id == log_id).first()
        if log_entry:
            log_entry.total_records_generated = total_records_generated
            log_entry.successful_count = successful_count
            log_entry.failed_count = failed_count
            log_entry.validated_records_count = validated_records_count
            log_entry.successful_generated_ids = successful_generated_ids
            db.commit()
            db.refresh(log_entry)
        return log_entry