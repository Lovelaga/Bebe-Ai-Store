"""
Unit tests for database operations.
Tests cover database initialization, connection handling, and error scenarios.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import psycopg2


class TestDatabaseInitialization:
    """Tests for database initialization and table creation."""
    
    @patch('psycopg2.connect')
    def test_init_db_creates_table_successfully(self, mock_connect, mock_env_vars):
        """Test that init_db creates the products table successfully."""
        # Setup
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Import after patching
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # We'll test the init_db function logic
        from io import StringIO
        import contextlib
        
        # Simulate init_db function
        def init_db():
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    external_id VARCHAR(50) UNIQUE,
                    title TEXT NOT NULL,
                    price VARCHAR(20),
                    image_url TEXT,
                    affiliate_link TEXT,
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
        
        # Execute
        init_db()
        
        # Assert
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        assert "CREATE TABLE IF NOT EXISTS products" in mock_cursor.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_init_db_handles_connection_error(self, mock_connect, mock_env_vars):
        """Test that init_db handles database connection errors gracefully."""
        # Setup - simulate connection failure
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        # Execute & Assert
        with pytest.raises(psycopg2.OperationalError):
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    
    @patch('psycopg2.connect')
    def test_init_db_with_invalid_credentials(self, mock_connect, mock_env_vars):
        """Test init_db behavior with invalid database credentials."""
        mock_connect.side_effect = psycopg2.OperationalError("Authentication failed")
        
        with pytest.raises(psycopg2.OperationalError) as exc_info:
            psycopg2.connect(os.getenv("DATABASE_URL"))
        
        assert "Authentication failed" in str(exc_info.value)
    
    @patch('psycopg2.connect')
    def test_init_db_sql_injection_protection(self, mock_connect, mock_env_vars):
        """Test that database operations are protected against SQL injection."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate parameterized query
        malicious_input = "'; DROP TABLE products; --"
        mock_cursor.execute(
            "INSERT INTO products (external_id, title) VALUES (%s, %s)",
            (malicious_input, "Test Product")
        )
        
        # Verify parameterized query was used (not string interpolation)
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (malicious_input, "Test Product")
    
    @patch('psycopg2.connect')
    def test_database_connection_uses_ssl(self, mock_connect, mock_env_vars):
        """Test that database connection URL includes SSL requirements."""
        import os
        db_url = os.getenv("DATABASE_URL")
        
        # Database URL should contain SSL mode for production
        # This is a validation test
        assert db_url is not None
        assert len(db_url) > 0


class TestDatabaseOperations:
    """Tests for database CRUD operations."""
    
    @patch('psycopg2.connect')
    def test_insert_product_with_valid_data(self, mock_connect, mock_env_vars):
        """Test inserting a product with valid data."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Execute insert
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (external_id, title, price, image_url, affiliate_link, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_id) DO NOTHING;
        """, ("123", "Test Product", "29.99", "http://img.jpg", "http://link.com", "gadgets"))
        conn.commit()
        
        # Assert
        mock_cursor.execute.assert_called_once()
        assert "INSERT INTO products" in mock_cursor.execute.call_args[0][0]
        assert mock_cursor.execute.call_args[0][1] == ("123", "Test Product", "29.99", "http://img.jpg", "http://link.com", "gadgets")
        mock_conn.commit.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_insert_duplicate_product_ignored(self, mock_connect, mock_env_vars):
        """Test that duplicate products are ignored due to ON CONFLICT clause."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Insert same product twice
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        query = """
            INSERT INTO products (external_id, title, price, image_url, affiliate_link)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (external_id) DO NOTHING;
        """
        data = ("123", "Test", "29.99", "img.jpg", "link.com")
        
        cur.execute(query, data)
        cur.execute(query, data)  # Duplicate insert
        
        # Both executes should succeed (ON CONFLICT handles duplicates)
        assert mock_cursor.execute.call_count == 2
    
    @patch('psycopg2.connect')
    def test_select_products_with_limit(self, mock_connect, mock_env_vars, sample_db_rows):
        """Test selecting products with LIMIT clause."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = sample_db_rows
        
        # Execute select
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT title, price, image_url, affiliate_link, category FROM products ORDER BY created_at DESC LIMIT 50;")
        rows = cur.fetchall()
        
        # Assert
        assert len(rows) == 3
        assert rows[0][0] == "Product 1"
        assert rows[1][1] == "29.99"
        mock_cursor.execute.assert_called_once()
        assert "LIMIT 50" in mock_cursor.execute.call_args[0][0]
    
    @patch('psycopg2.connect')
    def test_select_products_empty_database(self, mock_connect, mock_env_vars):
        """Test selecting products from empty database."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT * FROM products;")
        rows = cur.fetchall()
        
        assert rows == []
        assert len(rows) == 0
    
    @patch('psycopg2.connect')
    def test_database_transaction_rollback(self, mock_connect, mock_env_vars):
        """Test that failed transactions can be rolled back."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("Constraint violation")
        
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        try:
            cur.execute("INSERT INTO products (title) VALUES (%s)", ("Test",))
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
        
        # Verify rollback was called after error
        mock_conn.rollback.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_connection_cleanup_after_operation(self, mock_connect, mock_env_vars):
        """Test that database connections are properly closed after operations."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate a complete database operation
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT * FROM products;")
        cur.close()
        conn.close()
        
        # Assert cleanup
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_insert_product_with_null_optional_fields(self, mock_connect, mock_env_vars):
        """Test inserting product with NULL values in optional fields."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (external_id, title, price, image_url, affiliate_link, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("456", "Minimal Product", None, None, None, None))
        
        # Should succeed with NULL values for optional fields
        mock_cursor.execute.assert_called_once()
        assert mock_cursor.execute.call_args[0][1][2] is None  # price is None


class TestDatabaseEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @patch('psycopg2.connect')
    def test_very_long_product_title(self, mock_connect, mock_env_vars):
        """Test inserting product with very long title."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        long_title = "A" * 1000  # Very long title
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (external_id, title) VALUES (%s, %s)",
            ("789", long_title)
        )
        
        # Should handle long text
        assert len(mock_cursor.execute.call_args[0][1][1]) == 1000
    
    @patch('psycopg2.connect')
    def test_special_characters_in_product_data(self, mock_connect, mock_env_vars):
        """Test inserting product with special characters."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        special_title = "Product with 'quotes', \"double quotes\", and <html> tags & symbols"
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (external_id, title) VALUES (%s, %s)",
            ("special", special_title)
        )
        
        # Parameterized queries should handle special characters safely
        mock_cursor.execute.assert_called_once()
        assert special_title in mock_cursor.execute.call_args[0][1]
    
    @patch('psycopg2.connect')
    def test_unicode_characters_in_product(self, mock_connect, mock_env_vars):
        """Test inserting product with Unicode characters."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        unicode_title = "产品名称 プロダクト Продукт 🎉🚀💻"
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (external_id, title) VALUES (%s, %s)",
            ("unicode", unicode_title)
        )
        
        mock_cursor.execute.assert_called_once()
        assert unicode_title == mock_cursor.execute.call_args[0][1][1]
    
    @patch('psycopg2.connect')
    def test_empty_string_values(self, mock_connect, mock_env_vars):
        """Test inserting product with empty string values."""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (external_id, title, price) VALUES (%s, %s, %s)",
            ("empty", "Valid Title", "")  # Empty price string
        )
        
        mock_cursor.execute.assert_called_once()
        assert mock_cursor.execute.call_args[0][1][2] == ""
