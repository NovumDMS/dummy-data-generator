import random
import logging

from sqlalchemy.orm import Session

from app.helper.sales_order_helper import (
    get_client_main_location,
    get_random_items,
    get_random_taker,
    generate_order_no,
    get_ship_to_name,
    HDR_DEFAULT_STRUCTURE,
    LINE_DEFAULT_STRUCTURE,
)
from app.helper.file_helper import generate_tsv_file
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderCreate

logger = logging.getLogger(__name__)


def generate_sales_orders(order_data: SalesOrderCreate, db: Session, user_id: str, username: str) -> list[dict]:
    """Generate sales order header and line TSV files for the given parameters."""
    logger.info(f"Generating sales orders for client_id={order_data.client_id}, customer_id={order_data.customer_id}")

    client_id = order_data.client_id
    customer_id = order_data.customer_id
    customer_name = order_data.customer_name
    company_id = order_data.company_id
    ship_to_id = order_data.ship_to_id if order_data.ship_to_id else customer_id
    lower_item_count = order_data.lower_item_count
    upper_item_count = order_data.upper_item_count

    sales_order_count = (
        random.randint(1, 10)
        if order_data.sales_order_count == 0
        else order_data.sales_order_count
    )

    all_items: list[dict] = []
    final_generated_ids: list[str] = []

    logger.info(f"Generating {sales_order_count} sales order(s) with item counts between {lower_item_count} and {upper_item_count}")
    successful_count = 0
    failed_count = 0
    location_id = get_client_main_location(client_id, db)
    for i in range(sales_order_count):
        try:
            number_of_items = random.randint(lower_item_count, upper_item_count)

            taker = get_random_taker(client_id, db)
            items = get_random_items(client_id, number_of_items, db)
            import_set_no = i + 1

            order_no = generate_order_no()

            contact_id = items[0]["contact_id"] if items else None
            contact_name = items[0]["contact_name"] if items else None
            ship_to_name = get_ship_to_name(ship_to_id, client_id, db) if ship_to_id else None

            header_data = HDR_DEFAULT_STRUCTURE.copy()
            header_data.update({
                "import_set_no": import_set_no,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "company_id": company_id,
                "location_id": location_id,
                "contact_id": contact_id,
                "contact_name": contact_name,
                "taker": taker,
                "ship_to_id": ship_to_id,
                "ship_to_name": ship_to_name,
                "packing_basis": "partial",
                "quote": "N",
                "customer_po_no": f"PO{order_no}",
            })

            line_no = 1
            items_list = []
            for item in items:
                line_data = LINE_DEFAULT_STRUCTURE.copy()
                used_quantity = random.randint(1, int(item["qty_available"]))
                line_data.update({
                    "import_set_no": import_set_no,
                    "line_no": line_no,
                    "item_id": item["item_id"],
                    "unit_quantity": used_quantity,
                    "unit_of_measure": item["base_unit"],
                    "capture_usage": "Y",
                })
                line_no += 1
                items_list.append(line_data)
                item = dict(item)  # Convert from RowMapping to dict to update
                item["used_quantity"] = used_quantity
                all_items.append(item)

            generate_tsv_file([header_data], db, "SOH")
            final_generated_ids.append("SOH_" + str(import_set_no))
            generate_tsv_file(items_list, db, "SOL")
            final_generated_ids.append("SOL_" + str(import_set_no))
            successful_count += 1
        except Exception as e:
            logger.error(f"Error generating sales order line {i + 1}: {e}", exc_info=True)
            failed_count += 1
            continue
    GenerationLogs.log_so_generation(db, client_id, user_id, True, successful_count=successful_count, failed_count=failed_count, successful_generated_ids=final_generated_ids)
    return all_items
