import io
import logging
from datetime import datetime, timezone
import pandas as pd
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from config import settings
from database import products_collection, init_db
from nlp_utils import preprocess_title

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Bulk Upload API",
    description="A robust FastAPI system to parse bulk product Excel uploads, perform NLP cleansing, and upsert records into MongoDB natively.",
    version="1.0.0"
)

# Initialize database components on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Pydantic schemas for data validation and API response
class RowError(BaseModel):
    row: int
    sku: str
    reason: str

class UploadSummaryResponse(BaseModel):
    message: str
    status: str

# Async Email Notification Sub-Routine
async def send_email_notification(total_rows: int, inserted: int, updated: int, failed: int, timestamp: str):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    subject = "Product Bulk Upload Completed"
    body = f"""Hi,

Your product bulk upload has been processed successfully. Here is the summary:

  Total Rows    : {total_rows:,}
  Inserted       : {inserted:,}
  Updated        : {updated:,}
  Failed          : {failed:,}
  Uploaded At : {timestamp} UTC

Please review any failed rows in the application dashboard.

Regards,
Product Upload System"""

    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = settings.NOTIFY_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Using standard smtplib within an execution thread block safe for background tasks
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Notification email successfully dispatched to {settings.NOTIFY_EMAIL}")
    except Exception as e:
        # If email sending fails, log it but guarantee it won't impact upload processing metrics
        logger.error(f"Failed to send email notification: {e}")

# Core Background Business Logic Pipeline
def process_excel_upload_task(file_contents: bytes):
    from pymongo import UpdateOne
    
    REQUIRED_COLUMNS = {'title', 'sku', 'description', 'price'}
    
    # Initialize metrics counters
    total_rows = 0
    inserted = 0
    updated = 0
    failed = 0
    errors_list: List[dict] = []
    
    try:
        # Load the whole file structure using pandas engine
        excel_file = pd.ExcelFile(io.BytesIO(file_contents), engine='openpyxl')
        sheet_name = excel_file.sheet_names[0]
        
        # Read headers first to validate structural constraints before iterating chunks
        df_headers = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=0)
        missing_cols = REQUIRED_COLUMNS - set(df_headers.columns)
        if missing_cols:
            logger.error(f"Bulk processing stopped. Missing required columns: {missing_cols}")
            return

        # Deduplicate rows inside the file beforehand: last row occurrence takes priority
        df_all = pd.read_excel(excel_file, sheet_name=sheet_name)
        df_all = df_all.dropna(how='all') # Silently skip entirely empty rows
        total_rows = len(df_all)
        
        # Track duplicate lookups to keep the last occurrence index active
        df_all = df_all.loc[~df_all.index.duplicated(keep='last')]
        df_all = df_all.drop_duplicates(subset=['sku'], keep='last')
        
        # Process the clean file via customized environment chunk size parameters
        chunk_size = settings.CHUNK_SIZE
        chunks = [df_all[i:i + chunk_size] for i in range(0, len(df_all), chunk_size)]
        
        for chunk_idx, chunk in enumerate(chunks):
            bulk_operations = []
            chunk_errors = []
            
            for index, row in chunk.iterrows():
                # Add 2 to balance 0-based index conversion to standard Excel row visual numbers
                excel_row_num = index + 2 
                sku = str(row.get('sku', '')).strip()
                title = str(row.get('title', '')).strip()
                description = str(row.get('description', '')).strip()
                price_raw = row.get('price')

                # Row-level Field Validation Checkpoints
                if not sku or pd.isna(row.get('sku')):
                    failed += 1
                    errors_list.append({"row": excel_row_num, "sku": "UNKNOWN", "reason": "Missing SKU"})
                    continue
                if not title or pd.isna(row.get('title')):
                    failed += 1
                    errors_list.append({"row": excel_row_num, "sku": sku, "reason": "Missing title"})
                    continue
                if not description or pd.isna(row.get('description')):
                    failed += 1
                    errors_list.append({"row": excel_row_num, "sku": sku, "reason": "Missing description"})
                    continue
                
                # Numeric type sanity checks for variable prices
                try:
                    price = float(price_raw)
                    if pd.isna(price_raw):
                        raise ValueError()
                except (ValueError, TypeError):
                    failed += 1
                    errors_list.append({"row": excel_row_num, "sku": sku, "reason": "Missing or invalid non-numeric price"})
                    continue
                
                # Fire up NLP pre-processing utils
                formatted_title = preprocess_title(title)
                
                current_time = datetime.now(timezone.utc)
                
                # Setup core atomicity upsert queries
                # Use $setOnInsert for created_at, and $set for updating standard attributes
                op = UpdateOne(
                    {"sku": sku},
                    {
                        "$setOnInsert": {"created_at": current_time},
                        "$set": {
                            "title": title,
                            "formatted_title": formatted_title,
                            "description": description,
                            "price": price,
                            "updated_at": current_time
                        }
                    },
                    upsert=True
                )
                bulk_operations.append(op)
                
            # If valid operations are queued inside this chunk execution context
            if bulk_operations:
                try:
                    result = products_collection.bulk_write(bulk_operations, ordered=False)
                    # Quantify output data states using driver responses
                    inserted += result.upserted_count
                    updated += result.modified_count
                    
                    # If documents matched but didn't modify anything, consider it an updated/processed document status
                    # to keep numerical logic synchronized across summaries
                    unchanged_matches = result.matched_count - result.modified_count
                    updated += unchanged_matches
                    
                except Exception as bulk_ex:
                    logger.error(f"Partial chunk write failure in chunk segment index {chunk_idx}: {bulk_ex}")
                    # Capture unhandled internal failures to preserve execution of subsequent blocks
                    failed += len(bulk_operations)
                    
        # Log aggregated operational performance statistics
        completion_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Processing Complete: Total Rows={total_rows}, Inserted={inserted}, Updated={updated}, Failed={failed}")
        logger.info(f"Row Level Errors Tracked: {errors_list}")
        
        # Trigger explicit background context email routing components
        import asyncio
        asyncio.run(send_email_notification(total_rows, inserted, updated, failed, completion_time))

    except Exception as critical_err:
        logger.critical(f"Fatal error running background pipeline data calculations: {critical_err}")

# Endpoint Interface Route Entry
@app.post("/api/products/bulk-upload", response_model=UploadSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_products_bulk(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Accepts an Excel template file, executes basic validation rules, and yields control
    directly back to user client context while processing records asynchronously.
    """
    # Reject files containing non-Excel mime extensions
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unsupported File Type. Please provide a valid .xlsx or .xls document."
        )
        
    try:
        # Read binary file block synchronously into system RAM before delegating execution
        contents = await file.read()
        
        # Check basic schema parameters out-of-band to prevent queuing completely broken inputs
        df_headers = pd.read_excel(io.BytesIO(contents), nrows=0, engine='openpyxl')
        required_cols = {'title', 'sku', 'description', 'price'}
        missing_cols = required_cols - set(df_headers.columns)
        
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file schema structure. Missing required headers: {list(missing_cols)}"
            )
            
    except HTTPException as http_ex:
        raise http_ex
    except Exception as parse_ex:
        logger.error(f"File inspection checkpoint failed: {parse_ex}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to structurally parse spreadsheet file. Please check workbook configurations."
        )

    # Queue execution details safely out-of-line inside the background task loop threads
    background_tasks.add_task(process_excel_upload_task, contents)
    
    return {
        "message": "File uploaded successfully and queued for background processing. You will receive an email confirmation once processing is complete.",
        "status": "queued"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)