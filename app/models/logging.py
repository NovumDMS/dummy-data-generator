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
    generation_date = Column(DateTime)

    @staticmethod
    def log_so_generation(db, client_id: str, user_id: str, success_flag: bool, successful_count: int, failed_count: int, successful_generated_ids: list):
        """Log a new sales order generation event to the database"""
        new_log = GenerationLogs(
            id=gen_uuid(),
            client_id=client_id,
            user_id=user_id,
            generated_file_type="SO",
            success_flag=success_flag,
            total_records_generated=successful_count + failed_count,
            successful_count=successful_count,
            failed_count=failed_count,
            successful_generated_ids=successful_generated_ids,
            generation_date=datetime.now(timezone.utc)
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    
    @staticmethod
    def pull_so_logs(db):
        """Pull generation logs for a specific client and user"""
        logs = db.query(GenerationLogs).filter(GenerationLogs.generated_file_type == "SO" and GenerationLogs.success_flag == True).order_by(GenerationLogs.generation_date.desc()).all()
        formatted_logs = []
        for log in logs:
            formatted_log = {
                "id": str(log.id),
                "client_id": str(log.client_id),
                "user_id": str(log.user_id),
                "total_records_generated": log.total_records_generated,
                "successful_count": log.successful_count,
                "failed_count": log.failed_count,
                "validated_records_count": log.validated_records_count,
                "generation_date": log.generation_date.isoformat()
            }
            formatted_logs.append(formatted_log)
        return formatted_logs
    
    @staticmethod
    def log_po_generation(db, client_id: str, user_id: str, success_flag: bool, successful_count: int, failed_count: int, successful_generated_ids: list):
        """Log a new purchase order generation event to the database"""
        new_log = GenerationLogs(
            id=gen_uuid(),
            client_id=client_id,
            user_id=user_id,
            generated_file_type="PO",
            success_flag=success_flag,
            total_records_generated=successful_count + failed_count,
            successful_count=successful_count,
            failed_count=failed_count,
            successful_generated_ids=successful_generated_ids,
            generation_date=datetime.now(timezone.utc)
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    
    @staticmethod
    def pull_po_logs(db):
        """Pull generation logs for a specific client and user"""
        logs = db.query(GenerationLogs).filter(GenerationLogs.generated_file_type == "PO").order_by(GenerationLogs.generation_date.desc()).all()
        formatted_logs = []
        for log in logs:
            formatted_log = {
                "id": str(log.id),
                "client_id": str(log.client_id),
                "user_id": str(log.user_id),
                "total_records_generated": log.total_records_generated,
                "successful_count": log.successful_count,
                "failed_count": log.failed_count,
                "validated_records_count": log.validated_records_count,
                "generation_date": log.generation_date.isoformat()
            }
            formatted_logs.append(formatted_log)
        return formatted_logs

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