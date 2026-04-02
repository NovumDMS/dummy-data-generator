from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.access import login_required
from app.models.logging import GenerationLogs
from app.schemas import SalesOrderHdrCreate

from app.helper.sales_order_helper import get_client_main_location, get_random_items, get_random_taker, generate_order_no

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

@router.post("/generate")
@login_required
async def generate_sales_order_hdr(sales_order_data: SalesOrderHdrCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    """Endpoint to trigger sales order header generation"""
    # customer_id, company_id, location_id, ship_to_id, taker, order_date

    # Pull Customer ID, Company ID AND ship_to_id from the request body
    # Generate the Location ID, taker from the database based on p21s_location table and p21s_oe_hdr table.
    client_id = sales_order_data.client_id
    customer_id = sales_order_data.customer_id
    company_id = sales_order_data.company_id
    ship_to_id = sales_order_data.ship_to_id if sales_order_data.ship_to_id else customer_id
    number_of_items = sales_order_data.number_of_items  # For example, you can make this dynamic based on your needs

    location_id = await get_client_main_location(client_id, db)
    taker = await get_random_taker(client_id, db)
    items = await get_random_items(client_id, number_of_items, db)

    # Generate a unique order number starting in 98*****
    order_no = generate_order_no()

    # Generate header with the following details:
    # import_set_no, customer_id, customer_name, company_id, location_id, customer_po_no, 
    # contact_id, contact_name, taker, ship_to_id, ship_to_name

    # Generate line file with following detials:
    # import_set_no, line_no, item_id, unit_quantity, unit_of_measure, 

    generate_tsv_file(data, db)

def generate_tsv_file(data: dict, db: Session = Depends(get_db)):
    """Helper function to generate TSV file and log the generation"""
    # Simulate TSV file generation (in real implementation, you would create an actual file)
    tsv_content = "\t".join([f"{key}: {value}" for key, value in data.items()])
    
    # Log the generation in the database
    log_entry = GenerationLogs(
        client_id=data["customer_id"],
        company_id=data["company_id"],
        location_id=data["location_id"],
        ship_to_id=data["ship_to_id"],
        taker=data["taker"],
        order_date=data["order_date"],
        order_no=data["order_no"],
        po_no=data["po_no"]
    )
    db.add(log_entry)
    db.commit()
    logger.info(f"Generated TSV content: {tsv_content}")

 # *Import Set No*\t*Customer ID*\t*Customer Name*\t*Company ID*\t*Sales Location ID*\tCustomer PO Number\t
    # *Contact ID*\t*Contact Name*\t*Taker*\tJob Name\tOrder Date\tRequested Date\tQuote\tApproved\t*Ship To ID*\t
    # *Ship To Name*\tShip To Address 1\tShip To Address 2\tShip To City\tShip To State\tShip To Zip Code\t
    # Ship To Country\tSource Location ID\tCarrier ID\tCarrier Name\tRoute\t*Packing Basis*\tDelivery Instructions\t
    # Terms\tTerms Desc\tWill Call\tClass 1\tClass 2\tClass 3\tClass 4\tClass 5\tRMA_Flag\tFreight Code\t
    # Third Party Billing Flag Desc\tCapture Usage Default\tAllocate\tContract Number\tInvoice Batch Number\t
    # Ship To Email Address\tSet Invoice Exchange Rate Source Desc\tShip To Phone\tCurrency ID\t
    # Apply Builder Allowance Flag\tQuote Expiration Date\tPromise Date\tImport As Quote\tQuote Number\t
    # Web Reference Number\tCreate Invoice\tStrategic Pricing Library ID\tMerchandise Credit\tOrder Type Priority\t
    # UPS Code\tSupplier Order No\tSupplier Release No\tPlaced By Name\tReq Payment Upon Release\tFreight Out\t
    # Ship To Address\tQuote Type \tHomeowner \tInstaller\tBuilding\tArchitect \tDesigner \tPricing Source\t
    # Ship to Latitude\tShip To Longitude\t Exemption No\tOrder Number
def generate_so_hdr():
    header_data = f'{import_set_no}\t26242\t\tSHEPENT\t1075\t{po_num}\t\t\tB2BSELLER\t\t{order_date}\t{shipment_date}\tN\t\t{p21_ship_to_id}\t'
    header_data += f'{ship_to_name}\t{ship_to_address1}\t{ship_to_address2}\t{ship_to_city}\t{ship_to_state}\t{ship_to_postal_code}\t'
    header_data += f'{ship_to_country}\t1075\t\t\t\tPartial\t{bol_comments}\t\t\tN\t\t\t\t\t\tN\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t'
    header_data += f'\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t'


# *Import Set Number*\t*Line No*\t*Item ID*\t*Unit Quantity*\t*Unit of Measure*\tUnit Price\tExtended Description\t
    # Source Location ID\tShip Location ID\tProduct Group ID\tSupplier ID\tSupplier Name\tRequired Date\tExpedite Date\t
    # Will Call\tTax Item\tOK to Interchange\tPricing Unit\tCommission Cost\tOther Cost\tPO Cost\tDisposition\tScheduled\t
    # Manual Price Override\tCommission Cost Edited\tOther Cost Edited\t*Capture Usage*\tTag and Hold Class ID\t
    # Contract Bin ID\tContract No.\tAllocation Qty\tPromise Date\tRevision Level\tResolve Item Contract\tSample\t
    # Quote Line No.\tQuote Complete\tItem Description\tInvoice No.\tLine No
def generate_so_line():
    line_data = f'{import_set_no}\t{line_num}\t{item}\t{quantity}\t{validated_uom}\t'
    line_data += f'\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tY'
    so_line_data.append(line_data)
    line_num += 1