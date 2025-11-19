"""
Database management module for handling connections and operations.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self):
        """Initialize the database manager."""
        self.engines: Dict[str, AsyncEngine] = {}
        self.metadata = MetaData()
        self._initialize_default_databases()

    def _initialize_default_databases(self):
        """Initialize default database connections."""
        # Source database
        source_engine = create_async_engine(
            "sqlite+aiosqlite:///./data/source.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        self.engines["source"] = source_engine

        # Destination database
        dest_engine = create_async_engine(
            "sqlite+aiosqlite:///./data/destination.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        self.engines["destination"] = dest_engine

    async def get_engine(self, db_name: str) -> AsyncEngine:
        """
        Get database engine by name.

        Args:
            db_name: Name of the database

        Returns:
            Async database engine

        Raises:
            ValueError: If database name is not found
        """
        if db_name not in self.engines:
            raise ValueError(f"Database '{db_name}' not found")
        return self.engines[db_name]

    async def list_databases(self) -> Dict[str, List[str]]:
        """
        List all configured databases.

        Returns:
            Dictionary with database names
        """
        return {"databases": list(self.engines.keys()), "count": len(self.engines)}

    async def get_table_data(
        self, db_name: str, table_name: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from a table.

        Args:
            db_name: Database name
            table_name: Table name
            limit: Optional limit on number of records

        Returns:
            List of records as dictionaries
        """
        engine = await self.get_engine(db_name)

        async with engine.begin() as conn:
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            result = await conn.execute(text(query))
            rows = result.fetchall()

            # Convert rows to dictionaries
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]

    async def count_records(self, db_name: str, table_name: str) -> int:
        """
        Count records in a table.

        Args:
            db_name: Database name
            table_name: Table name

        Returns:
            Number of records
        """
        engine = await self.get_engine(db_name)

        async with engine.begin() as conn:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            return count or 0

    async def insert_batch(
        self, db_name: str, table_name: str, records: List[Dict[str, Any]]
    ) -> int:
        """
        Insert a batch of records into a table.

        Args:
            db_name: Database name
            table_name: Table name
            records: List of records to insert

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        engine = await self.get_engine(db_name)

        async with engine.begin() as conn:
            # Build insert statement
            columns = list(records[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])
            columns_str = ", ".join(columns)

            insert_query = (
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            )

            # Execute batch insert
            await conn.execute(text(insert_query), records)

        return len(records)

    async def table_exists(self, db_name: str, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            db_name: Database name
            table_name: Table name

        Returns:
            True if table exists, False otherwise
        """
        engine = await self.get_engine(db_name)

        async with engine.begin() as conn:
            if "sqlite" in str(engine.url):
                query = """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=:table_name
                """
            else:
                query = """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name=:table_name
                """

            result = await conn.execute(text(query), {"table_name": table_name})
            return result.fetchone() is not None

    async def create_table_from_schema(
        self, db_name: str, table_name: str, columns: Dict[str, str]
    ):
        """
        Create a table with specified schema.

        Args:
            db_name: Database name
            table_name: Table name
            columns: Dictionary of column names to types
        """
        engine = await self.get_engine(db_name)

        # Build CREATE TABLE statement
        column_defs = []
        for col_name, col_type in columns.items():
            column_defs.append(f"{col_name} {col_type}")

        create_query = (
            f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        )

        async with engine.begin() as conn:
            await conn.execute(text(create_query))

        logger.info(f"Created table {table_name} in {db_name}")

    async def initialize_sample_data(self):
        """Initialize sample databases with test data."""
        import os

        # Create data directory
        os.makedirs("./data", exist_ok=True)

        # Create sample table in source database
        await self.create_table_from_schema(
            "source",
            "users",
            {
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "email": "TEXT NOT NULL",
                "age": "INTEGER",
                "salary": "REAL",
            },
        )

        # Insert sample data
        sample_users = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "salary": 75000.0,
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "age": 28,
                "salary": 82000.0,
            },
            {
                "id": 3,
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "age": 35,
                "salary": 95000.0,
            },
            {
                "id": 4,
                "name": "Alice Williams",
                "email": "alice@example.com",
                "age": 32,
                "salary": 88000.0,
            },
            {
                "id": 5,
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "age": 29,
                "salary": 71000.0,
            },
        ]

        # Check if data already exists
        count = await self.count_records("source", "users")
        if count == 0:
            await self.insert_batch("source", "users", sample_users)
            logger.info(
                f"Inserted {len(sample_users)} sample users into source database"
            )
        else:
            logger.info(
                f"Sample data already exists in source database ({count} records)"
            )

        # Create destination table structure (empty)
        await self.create_table_from_schema(
            "destination",
            "users_copy",
            {
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "email": "TEXT NOT NULL",
                "age": "INTEGER",
                "salary": "REAL",
            },
        )

        logger.info("Sample databases initialized successfully")

    async def close_all(self):
        """Close all database connections."""
        for name, engine in self.engines.items():
            await engine.dispose()
            logger.info(f"Closed connection to {name}")
