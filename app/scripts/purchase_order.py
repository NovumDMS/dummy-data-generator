import logging

from sqlalchemy.orm import Session

from app.schemas import PurchaseOrderCreate
from app.helper.purchase_order_helper import build_purchase_order_payload
from app.helper.file_helper import generate_tsv_file

logger = logging.getLogger(__name__)


def generate_purchase_orders(order_data: PurchaseOrderCreate, db: Session) -> None:
    """Generate purchase order header and line TSV files grouped by supplier."""
    order_payload = order_data.model_dump()

    # Accept either a raw list of sales-order line items or a dict wrapper.
    raw_item_data = order_payload.get("item_data")
    if isinstance(raw_item_data, list):
        source_items = raw_item_data
    elif isinstance(raw_item_data, dict):
        source_items = raw_item_data.get("items", [])
    else:
        source_items = []

    purchase_orders = build_purchase_order_payload(order_payload, source_items, db)

    for po in purchase_orders:
        generate_tsv_file([po["header"]], db, "POH")
        generate_tsv_file(po["organized_items"], db, "POL")

    logger.info("Generated %d purchase order(s) for client %s", len(purchase_orders), order_data.client_id)
