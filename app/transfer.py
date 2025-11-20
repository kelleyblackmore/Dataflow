"""
Data transfer service for moving data between databases.
"""

import logging
import uuid
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from app.database import DatabaseManager
from app.models import TransferConfig, TransferStatus

logger = logging.getLogger(__name__)


class DataTransferService:
    """Service for transferring data between databases."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the transfer service.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.transfers: Dict[str, TransferStatus] = {}
        self._transfer_lock = asyncio.Lock()

    async def transfer_data(self, config: TransferConfig) -> TransferStatus:
        """
        Transfer data from source to destination database.

        Args:
            config: Transfer configuration

        Returns:
            Transfer status
        """
        # Generate transfer ID
        transfer_id = f"txn_{uuid.uuid4().hex[:12]}"

        # Create initial status
        status = TransferStatus(
            transfer_id=transfer_id,
            status="running",
            source_table=config.source_table,
            destination_table=config.destination_table,
            records_transferred=0,
            total_records=0,
            started_at=datetime.now(),
        )

        async with self._transfer_lock:
            self.transfers[transfer_id] = status

        try:
            logger.info(
                f"Starting transfer {transfer_id}: {config.source_table} -> {config.destination_table}"
            )

            # Check if source table exists
            source_exists = await self.db_manager.table_exists(
                config.source_db, config.source_table
            )
            if not source_exists:
                raise ValueError(
                    f"Source table '{config.source_table}' does not exist in database '{config.source_db}'. "
                    "Please check the database and table names and ensure the table exists."
                )

            # Count total records in source
            total_records = await self.db_manager.count_records(
                config.source_db, config.source_table
            )
            status.total_records = total_records

            if total_records == 0:
                logger.warning(
                    f"No records found in source table {config.source_table}"
                )
                status.status = "completed"
                status.completed_at = datetime.now()
                return status

            # Check if destination table exists, if not create it
            dest_exists = await self.db_manager.table_exists(
                config.destination_db, config.destination_table
            )
            if not dest_exists:
                # Get schema from source table
                sample_data = await self.db_manager.get_table_data(
                    config.source_db, config.source_table, limit=1
                )
                if sample_data:
                    # Infer schema from first row
                    schema = {}
                    for key, value in sample_data[0].items():
                        if isinstance(value, int):
                            schema[key] = "INTEGER"
                        elif isinstance(value, float):
                            schema[key] = "REAL"
                        else:
                            schema[key] = "TEXT"

                    await self.db_manager.create_table_from_schema(
                        config.destination_db, config.destination_table, schema
                    )

            # Transfer data in batches with transaction support
            offset = 0
            batch_size = config.batch_size

            # Get engine once for the entire transfer
            source_engine = await self.db_manager.get_engine(config.source_db)

            while offset < total_records:
                # Fetch batch from source using parameterized query
                async with source_engine.connect() as conn:
                    from sqlalchemy import text

                    # Use identifier() for safe table name handling
                    result = await conn.execute(
                        text(
                            f"SELECT * FROM {config.source_table} LIMIT :limit OFFSET :offset"
                        ),
                        {"limit": batch_size, "offset": offset},
                    )
                    rows = result.fetchall()
                    columns = result.keys()
                    batch_data = [dict(zip(columns, row)) for row in rows]

                if not batch_data:
                    break

                # Insert batch into destination within a transaction
                try:
                    records_inserted = await self.db_manager.insert_batch(
                        config.destination_db, config.destination_table, batch_data
                    )

                    async with self._transfer_lock:
                        status.records_transferred += records_inserted
                    offset += batch_size

                    logger.info(
                        f"Transfer {transfer_id}: {status.records_transferred}/{total_records} records transferred"
                    )
                except Exception as batch_error:
                    logger.error(
                        f"Failed to insert batch at offset {offset}: {str(batch_error)}"
                    )
                    raise

            # Mark as completed
            status.status = "completed"
            status.completed_at = datetime.now()

            logger.info(
                f"Transfer {transfer_id} completed successfully: {status.records_transferred} records transferred"
            )

        except Exception as e:
            logger.error(f"Transfer {transfer_id} failed: {str(e)}")
            async with self._transfer_lock:
                status.status = "failed"
                status.error_message = str(e)
                status.completed_at = datetime.now()
            # Return the failed status instead of raising to provide consistent API response
            return status

        return status

    async def get_status(self, transfer_id: str) -> Optional[TransferStatus]:
        """
        Get the status of a transfer operation.

        Args:
            transfer_id: Transfer identifier

        Returns:
            Transfer status or None if not found
        """
        async with self._transfer_lock:
            return self.transfers.get(transfer_id)

    async def get_all_transfers(self) -> List[TransferStatus]:
        """
        Get all transfer operations.

        Returns:
            List of all transfer statuses
        """
        async with self._transfer_lock:
            return list(self.transfers.values())
