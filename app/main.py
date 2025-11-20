"""
FastAPI application for data transfer between databases with visual flow representation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.database import DatabaseManager
from app.transfer import DataTransferService
from app.visualization import create_flow_diagram
from app.models import TransferConfig, TransferStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DataFlow - Database Transfer Service",
    description="Transfer data between databases and visualize the flow",
    version="1.0.0",
)

# Add CORS middleware with configurable origins
# In production, set ALLOWED_ORIGINS environment variable to specific origins
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize services
db_manager = DatabaseManager()
transfer_service = DataTransferService(db_manager)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    await db_manager.close_all()
    logger.info("Application shutdown - resources cleaned up")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with application information."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DataFlow - Database Transfer Service</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #333;
            }
            .endpoint {
                background-color: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .method {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 10px;
            }
            .get { background-color: #61affe; color: white; }
            .post { background-color: #49cc90; color: white; }
            code {
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <h1>🔄 DataFlow - Database Transfer Service</h1>
        <p>Welcome to the DataFlow API. This service allows you to transfer data between databases and visualize the flow.</p>

        <h2>Available Endpoints:</h2>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/docs</code>
            <p>Interactive API documentation (Swagger UI)</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/health</code>
            <p>Check service health status</p>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/transfer</code>
            <p>Transfer data from source to destination database</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/transfer/status/{transfer_id}</code>
            <p>Get status of a data transfer operation</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/flow/visualize</code>
            <p>Visualize the data flow diagram</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/databases/list</code>
            <p>List all configured database connections</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "DataFlow", "version": "1.0.0"}


@app.post("/transfer", response_model=TransferStatus)
async def transfer_data(config: TransferConfig):
    """
    Transfer data from source database to destination database.

    Args:
        config: Transfer configuration including source, destination, and table info

    Returns:
        Transfer status with operation details
    """
    try:
        logger.info(
            f"Starting data transfer: {config.source_table} -> {config.destination_table}"
        )
        result = await transfer_service.transfer_data(config)
        return result
    except Exception as e:
        logger.error(f"Transfer failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@app.get("/transfer/status/{transfer_id}", response_model=TransferStatus)
async def get_transfer_status(transfer_id: str):
    """
    Get the status of a specific transfer operation.

    Args:
        transfer_id: Unique identifier of the transfer operation

    Returns:
        Current status of the transfer
    """
    status = await transfer_service.get_status(transfer_id)
    if not status:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return status


@app.get("/flow/visualize", response_class=HTMLResponse)
async def visualize_flow():
    """
    Generate and display a visual representation of the data flow.

    Returns:
        HTML page with interactive flow diagram
    """
    try:
        transfers = await transfer_service.get_all_transfers()
        html_content = create_flow_diagram(transfers)
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Failed to generate visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@app.get("/databases/list")
async def list_databases():
    """
    List all configured database connections.

    Returns:
        Dictionary with database names and count
    """
    try:
        databases = await db_manager.list_databases()
        return databases
    except Exception as e:
        logger.error(f"Failed to list databases: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list databases: {str(e)}"
        )


@app.post("/databases/initialize")
async def initialize_sample_databases():
    """
    Initialize sample databases with test data for demonstration purposes.

    Returns:
        Confirmation message
    """
    try:
        await db_manager.initialize_sample_data()
        return {
            "status": "success",
            "message": "Sample databases initialized with test data",
        }
    except Exception as e:
        logger.error(f"Failed to initialize databases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
