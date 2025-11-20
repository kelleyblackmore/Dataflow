"""
Data models for the DataFlow application.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


class DatabaseType(str, Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class DatabaseConfig(BaseModel):
    """Configuration for a database connection."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "source_db",
                "db_type": "sqlite",
                "connection_string": "sqlite:///./data/source.db",
            }
        }
    )

    name: str = Field(..., description="Database connection name")
    db_type: DatabaseType = Field(
        default=DatabaseType.SQLITE, description="Database type"
    )
    connection_string: str = Field(..., description="Database connection string")


class TransferConfig(BaseModel):
    """Configuration for a data transfer operation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_db": "source",
                "destination_db": "destination",
                "source_table": "users",
                "destination_table": "users_copy",
                "batch_size": 1000,
            }
        }
    )

    source_db: str = Field(default="source", description="Source database name")
    destination_db: str = Field(
        default="destination", description="Destination database name"
    )
    source_table: str = Field(..., description="Source table name")
    destination_table: str = Field(..., description="Destination table name")
    batch_size: int = Field(
        default=1000, description="Number of records to transfer in each batch", ge=1
    )

    @field_validator("source_db", "destination_db", "source_table", "destination_table")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate that database and table names are safe identifiers."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                f"Invalid identifier '{v}'. Must contain only alphanumeric characters and underscores, "
                "and must not start with a number."
            )
        return v


class TransferStatus(BaseModel):
    """Status of a data transfer operation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transfer_id": "txn_123456",
                "status": "completed",
                "source_table": "users",
                "destination_table": "users_copy",
                "records_transferred": 1000,
                "total_records": 1000,
                "started_at": "2024-01-01T12:00:00",
                "completed_at": "2024-01-01T12:00:30",
                "error_message": None,
            }
        }
    )

    transfer_id: str = Field(..., description="Unique identifier for the transfer")
    status: str = Field(
        ..., description="Current status (pending, running, completed, failed)"
    )
    source_table: str = Field(..., description="Source table name")
    destination_table: str = Field(..., description="Destination table name")
    records_transferred: int = Field(
        default=0, description="Number of records transferred"
    )
    total_records: int = Field(
        default=0, description="Total number of records to transfer"
    )
    started_at: datetime = Field(
        default_factory=datetime.now, description="Transfer start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Transfer completion time"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if transfer failed"
    )


class FlowNode(BaseModel):
    """Represents a node in the data flow diagram."""

    id: str = Field(..., description="Node identifier")
    label: str = Field(..., description="Node display label")
    node_type: str = Field(..., description="Type of node (database, table, process)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class FlowEdge(BaseModel):
    """Represents an edge (connection) in the data flow diagram."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: Optional[str] = Field(default=None, description="Edge label")
    records: Optional[int] = Field(
        default=None, description="Number of records transferred"
    )
