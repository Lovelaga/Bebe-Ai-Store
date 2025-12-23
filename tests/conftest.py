"""
Shared test fixtures and configuration for the test suite.
"""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
import psycopg2


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
    monkeypatch.setenv("ALI_KEY", "test_ali_key_12345")
    monkeypatch.setenv("ALI_SECRET", "test_ali_secret_67890")


@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    return mock_conn, mock_cursor


@pytest.fixture
def mock_aliexpress_api():
    """Mock AliExpress API client."""
    mock_api = MagicMock()
    mock_response = MagicMock()
    mock_response.products = []
    mock_api.get_products.return_value = mock_response
    return mock_api


@pytest.fixture
def sample_product():
    """Sample product data for testing."""
    product = MagicMock()
    product.product_id = "123456789"
    product.product_title = "Wireless Bluetooth Earphones"
    product.target_sale_price = "29.99"
    product.product_main_image_url = "https://example.com/image.jpg"
    product.promotion_link = "https://aliexpress.com/affiliate/link"
    product.product_detail_url = "https://aliexpress.com/item/123456789.html"
    return product


@pytest.fixture
def sample_products_list(sample_product):
    """List of sample products for testing."""
    products = []
    for i in range(5):
        prod = MagicMock()
        prod.product_id = f"12345678{i}"
        prod.product_title = f"Test Product {i}"
        prod.target_sale_price = f"{20 + i}.99"
        prod.product_main_image_url = f"https://example.com/image{i}.jpg"
        prod.promotion_link = f"https://aliexpress.com/affiliate/link{i}"
        prod.product_detail_url = f"https://aliexpress.com/item/12345678{i}.html"
        products.append(prod)
    return products


@pytest.fixture
def sample_db_rows():
    """Sample database rows for testing."""
    return [
        ("Product 1", "19.99", "https://example.com/img1.jpg", "https://link1.com", "smart watch"),
        ("Product 2", "29.99", "https://example.com/img2.jpg", "https://link2.com", "earbuds"),
        ("Product 3", "39.99", "https://example.com/img3.jpg", "https://link3.com", "drone"),
    ]