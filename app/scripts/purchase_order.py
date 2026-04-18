import logging

from sqlalchemy.orm import Session

from app.schemas import PurchaseOrderCreate
from app.helper.purchase_order_helper import build_purchase_order_payload
from app.helper.file_helper import generate_tsv_file

logger = logging.getLogger(__name__)


def generate_purchase_orders(order_data: PurchaseOrderCreate, user_id: str, db: Session) -> None:
    """Generate purchase order header and line TSV files grouped by supplier."""

    purchase_orders = build_purchase_order_payload(order_data, user_id, db)

    for po in purchase_orders:
        generate_tsv_file([po["header"]], db, "POH")
        generate_tsv_file(po["lines"], db, "POL")

    logger.info("Generated %d purchase order(s) for client %s", len(purchase_orders), order_data.client_id)
