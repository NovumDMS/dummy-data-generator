import logging

from sqlalchemy.orm import Session

from app.schemas import PurchaseOrderCreate

logger = logging.getLogger(__name__)


def generate_purchase_orders(order_data: PurchaseOrderCreate, db: Session) -> None:
    """Generate purchase order header and line TSV files. Implementation pending."""
    logger.info("Purchase order generation not yet implemented for client %s", order_data.client_id)
