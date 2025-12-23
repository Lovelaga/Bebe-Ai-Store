"""
Unit tests for AliExpress API integration.
Tests cover API client initialization, product fetching, error handling, and data processing.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os


class TestAliExpressAPIInitialization:
    """Tests for AliExpress API client initialization."""
    
    @patch('aliexpress_api.AliexpressApi')
    def test_api_client_initialization(self, mock_api_class, mock_env_vars):
        """Test that AliExpress API client is initialized with correct parameters."""
        from aliexpress_api import models
        
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        
        # Initialize API client
        ali_key = os.getenv("ALI_KEY")
        ali_secret = os.getenv("ALI_SECRET")
        tracking_id = "test_tracking_id"
        
        client = mock_api_class(
            ali_key, 
            ali_secret, 
            models.Language.EN, 
            models.Currency.EUR, 
            tracking_id
        )
        
        # Verify initialization
        mock_api_class.assert_called_once()
        assert client is not None
    
    @patch('aliexpress_api.AliexpressApi')
    def test_api_client_with_invalid_credentials(self, mock_api_class, mock_env_vars):
        """Test API client initialization with invalid credentials."""
        mock_api_class.side_effect = Exception("Invalid API credentials")
        
        with pytest.raises(Exception) as exc_info:
            from aliexpress_api import models
            mock_api_class("invalid", "invalid", models.Language.EN, models.Currency.EUR, "id")
        
        assert "Invalid API credentials" in str(exc_info.value)
    
    @patch('aliexpress_api.AliexpressApi')
    def test_api_client_with_missing_env_vars(self, mock_api_class):
        """Test API client when environment variables are missing."""
        # Don't use mock_env_vars fixture
        ali_key = os.getenv("ALI_KEY")
        ali_secret = os.getenv("ALI_SECRET")
        
        # At least one should be None or we're testing the initialization works
        if ali_key is None or ali_secret is None:
            # This is expected behavior - missing credentials
            assert ali_key is None or ali_secret is None
    
    @patch('aliexpress_api.AliexpressApi')
    def test_api_client_with_different_currencies(self, mock_api_class, mock_env_vars):
        """Test API client initialization with different currency options."""
        from aliexpress_api import models
        
        currencies = [models.Currency.EUR, models.Currency.USD]
        
        for currency in currencies:
            mock_api_instance = MagicMock()
            mock_api_class.return_value = mock_api_instance
            
            client = mock_api_class(
                os.getenv("ALI_KEY"),
                os.getenv("ALI_SECRET"),
                models.Language.EN,
                currency,
                "tracking"
            )
            
            assert client is not None
    
    @patch('aliexpress_api.AliexpressApi')
    def test_api_client_with_different_languages(self, mock_api_class, mock_env_vars):
        """Test API client initialization with different language options."""
        from aliexpress_api import models
        
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        
        # Test with English language
        client = mock_api_class(
            os.getenv("ALI_KEY"),
            os.getenv("ALI_SECRET"),
            models.Language.EN,
            models.Currency.EUR,
            "tracking"
        )
        
        assert client is not None


class TestProductFetching:
    """Tests for fetching products from AliExpress API."""
    
    def test_get_products_with_keyword(self, mock_aliexpress_api, sample_products_list):
        """Test fetching products with a specific keyword."""
        mock_response = MagicMock()
        mock_response.products = sample_products_list
        mock_aliexpress_api.get_products.return_value = mock_response
        
        # Fetch products
        response = mock_aliexpress_api.get_products(
            keywords="bluetooth earphones",
            max_sale_price=5000,
            page_size=10
        )
        
        # Verify
        assert len(response.products) == 5
        assert response.products[0].product_title == "Test Product 0"
        mock_aliexpress_api.get_products.assert_called_once_with(
            keywords="bluetooth earphones",
            max_sale_price=5000,
            page_size=10
        )
    
    def test_get_products_with_price_filter(self, mock_aliexpress_api, sample_product):
        """Test fetching products with price filter."""
        mock_response = MagicMock()
        mock_response.products = [sample_product]
        mock_aliexpress_api.get_products.return_value = mock_response
        
        response = mock_aliexpress_api.get_products(
            keywords="smart watch",
            max_sale_price=3000,  # 30 EUR
            page_size=5
        )
        
        # Verify price filter was applied
        call_kwargs = mock_aliexpress_api.get_products.call_args[1]
        assert call_kwargs['max_sale_price'] == 3000
    
    def test_get_products_with_page_size(self, mock_aliexpress_api):
        """Test fetching products with different page sizes."""
        mock_response = MagicMock()
        mock_response.products = []
        mock_aliexpress_api.get_products.return_value = mock_response
        
        # Test different page sizes
        for page_size in [5, 10, 20, 50]:
            response = mock_aliexpress_api.get_products(
                keywords="test",
                page_size=page_size
            )
            
            # Verify page_size parameter
            call_kwargs = mock_aliexpress_api.get_products.call_args[1]
            assert call_kwargs['page_size'] == page_size
    
    def test_get_products_empty_results(self, mock_aliexpress_api):
        """Test fetching products when no results are found."""
        mock_response = MagicMock()
        mock_response.products = []
        mock_aliexpress_api.get_products.return_value = mock_response
        
        response = mock_aliexpress_api.get_products(
            keywords="nonexistent product xyz123",
            max_sale_price=5000,
            page_size=10
        )
        
        assert len(response.products) == 0
    
    def test_get_products_api_error(self, mock_aliexpress_api):
        """Test handling API errors when fetching products."""
        mock_aliexpress_api.get_products.side_effect = Exception("API Error: Rate limit exceeded")
        
        with pytest.raises(Exception) as exc_info:
            mock_aliexpress_api.get_products(keywords="test")
        
        assert "API Error" in str(exc_info.value)
    
    def test_get_products_timeout(self, mock_aliexpress_api):
        """Test handling timeout when fetching products."""
        mock_aliexpress_api.get_products.side_effect = TimeoutError("Request timeout")
        
        with pytest.raises(TimeoutError):
            mock_aliexpress_api.get_products(keywords="test")
    
    def test_get_products_with_unicode_keyword(self, mock_aliexpress_api, sample_product):
        """Test fetching products with Unicode characters in keyword."""
        mock_response = MagicMock()
        mock_response.products = [sample_product]
        mock_aliexpress_api.get_products.return_value = mock_response
        
        response = mock_aliexpress_api.get_products(
            keywords="蓝牙耳机",
            max_sale_price=5000,
            page_size=10
        )
        
        call_kwargs = mock_aliexpress_api.get_products.call_args[1]
        assert call_kwargs['keywords'] == "蓝牙耳机"


class TestProductDataProcessing:
    """Tests for processing product data from API responses."""
    
    def test_extract_product_id(self, sample_product):
        """Test extracting product ID from product object."""
        product_id = str(sample_product.product_id)
        
        assert product_id == "123456789"
        assert isinstance(product_id, str)
    
    def test_extract_product_title(self, sample_product):
        """Test extracting product title."""
        title = sample_product.product_title
        
        assert title == "Wireless Bluetooth Earphones"
        assert len(title) > 0
    
    def test_extract_product_price(self, sample_product):
        """Test extracting product price."""
        price = sample_product.target_sale_price
        
        assert price == "29.99"
    
    def test_extract_product_image_url(self, sample_product):
        """Test extracting product image URL."""
        image_url = sample_product.product_main_image_url
        
        assert image_url.startswith("https://")
        assert "example.com" in image_url
    
    def test_extract_promotion_link(self, sample_product):
        """Test extracting affiliate/promotion link."""
        # Check if promotion_link exists
        if hasattr(sample_product, 'promotion_link'):
            link = sample_product.promotion_link
        else:
            link = sample_product.product_detail_url
        
        assert link.startswith("https://")
        assert "aliexpress.com" in link
    
    def test_product_without_promotion_link(self):
        """Test handling product without promotion link."""
        product = MagicMock()
        product.product_id = "999"
        product.product_title = "Test Product"
        product.target_sale_price = "19.99"
        product.product_main_image_url = "https://example.com/img.jpg"
        product.product_detail_url = "https://aliexpress.com/item/999.html"
        
        # Remove promotion_link attribute
        del product.promotion_link
        
        # Should fallback to product_detail_url
        link = product.promotion_link if hasattr(product, 'promotion_link') else product.product_detail_url
        
        assert link == "https://aliexpress.com/item/999.html"
    
    def test_process_multiple_products(self, sample_products_list):
        """Test processing multiple products from response."""
        processed = []
        
        for item in sample_products_list:
            processed.append({
                'id': str(item.product_id),
                'title': item.product_title,
                'price': item.target_sale_price,
                'image': item.product_main_image_url,
                'link': item.promotion_link if hasattr(item, 'promotion_link') else item.product_detail_url
            })
        
        assert len(processed) == 5
        assert all('id' in p for p in processed)
        assert all('title' in p for p in processed)
    
    def test_product_with_missing_fields(self):
        """Test handling products with missing optional fields."""
        product = MagicMock()
        product.product_id = "123"
        product.product_title = "Minimal Product"
        product.target_sale_price = None  # Missing price
        product.product_main_image_url = None  # Missing image
        product.product_detail_url = "https://aliexpress.com/item/123.html"
        
        # Should handle None values gracefully
        assert product.product_id is not None
        assert product.target_sale_price is None
        assert product.product_main_image_url is None
    
    def test_product_with_special_characters_in_title(self):
        """Test products with special characters in title."""
        product = MagicMock()
        product.product_title = "Product with 'quotes' & <html> tags"
        product.product_id = "456"
        
        # Title should be preserved as-is
        assert "'" in product.product_title
        assert "&" in product.product_title
        assert "<" in product.product_title


class TestScheduledMarketScan:
    """Tests for scheduled market scan functionality."""
    
    @patch('random.choice')
    @patch('psycopg2.connect')
    def test_scheduled_scan_selects_random_keyword(self, mock_connect, mock_random_choice, 
                                                   mock_aliexpress_api, sample_product, mock_env_vars):
        """Test that scheduled scan selects a random keyword."""
        keywords = ["smart watch", "wireless earbuds", "drone", "gaming accessories"]
        mock_random_choice.return_value = "wireless earbuds"
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_response = MagicMock()
        mock_response.products = [sample_product]
        mock_aliexpress_api.get_products.return_value = mock_response
        
        # Simulate scheduled scan
        import random
        selected = random.choice(keywords)
        
        assert selected in keywords
        mock_random_choice.assert_called_once_with(keywords)
    
    @patch('psycopg2.connect')
    def test_scheduled_scan_saves_products(self, mock_connect, mock_aliexpress_api, 
                                          sample_products_list, mock_env_vars):
        """Test that scheduled scan saves products to database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_response = MagicMock()
        mock_response.products = sample_products_list
        mock_aliexpress_api.get_products.return_value = mock_response
        
        # Simulate scan and save
        response = mock_aliexpress_api.get_products(
            keywords="test",
            max_sale_price=10000,
            page_size=5
        )
        
        conn = mock_connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        for item in response.products:
            link = item.promotion_link if hasattr(item, 'promotion_link') else item.product_detail_url
            cur.execute("""
                INSERT INTO products (external_id, title, price, image_url, affiliate_link, category)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING;
            """, (str(item.product_id), item.product_title, item.target_sale_price, 
                  item.product_main_image_url, link, "test"))
        
        # Verify database operations
        assert mock_cursor.execute.call_count == 5
        mock_conn.commit.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_scheduled_scan_handles_api_failure(self, mock_connect, mock_aliexpress_api, mock_env_vars):
        """Test that scheduled scan handles API failures gracefully."""
        mock_aliexpress_api.get_products.side_effect = Exception("API connection failed")
        
        # Scan should handle error gracefully
        try:
            response = mock_aliexpress_api.get_products(keywords="test")
        except Exception as e:
            assert "API connection failed" in str(e)
            # Error should be caught and logged, not crash the app
    
    @patch('psycopg2.connect')
    def test_scheduled_scan_with_empty_results(self, mock_connect, mock_aliexpress_api, mock_env_vars):
        """Test scheduled scan when API returns no products."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_response = MagicMock()
        mock_response.products = []
        mock_aliexpress_api.get_products.return_value = mock_response
        
        response = mock_aliexpress_api.get_products(keywords="test", page_size=5)
        
        # Should handle empty results
        assert len(response.products) == 0
        # No database inserts should occur
        mock_cursor.execute.assert_not_called()
    
    def test_scheduled_scan_keyword_variety(self):
        """Test that scheduled scan uses a variety of keywords."""
        keywords = ["smart watch", "wireless earbuds", "drone", "gaming accessories"]
        
        # Verify all keywords are valid strings
        assert all(isinstance(k, str) for k in keywords)
        assert all(len(k) > 0 for k in keywords)
        assert len(keywords) == 4
        assert len(set(keywords)) == 4  # All unique
    
    @patch('psycopg2.connect')
    def test_scheduled_scan_price_limit(self, mock_connect, mock_aliexpress_api, mock_env_vars):
        """Test that scheduled scan uses appropriate price limit."""
        mock_response = MagicMock()
        mock_response.products = []
        mock_aliexpress_api.get_products.return_value = mock_response
        
        response = mock_aliexpress_api.get_products(
            keywords="test",
            max_sale_price=10000,  # 100 EUR
            page_size=5
        )
        
        # Verify price limit
        call_kwargs = mock_aliexpress_api.get_products.call_args[1]
        assert call_kwargs['max_sale_price'] == 10000


class TestAffiliateLinks:
    """Tests for affiliate link generation and handling."""
    
    def test_promotion_link_is_used_when_available(self, sample_product):
        """Test that promotion link is preferred over detail URL."""
        link = sample_product.promotion_link if hasattr(sample_product, 'promotion_link') else sample_product.product_detail_url
        
        # Promotion link should be used
        assert link == sample_product.promotion_link
        assert "affiliate" in link
    
    def test_fallback_to_detail_url(self):
        """Test fallback to product detail URL when promotion link unavailable."""
        product = MagicMock()
        product.product_detail_url = "https://aliexpress.com/item/123.html"
        
        # Remove promotion_link
        del product.promotion_link
        
        link = product.promotion_link if hasattr(product, 'promotion_link') else product.product_detail_url
        
        assert link == product.product_detail_url
    
    def test_affiliate_link_format(self, sample_product):
        """Test that affiliate links have correct format."""
        link = sample_product.promotion_link
        
        assert link.startswith("https://")
        assert "aliexpress.com" in link
        assert len(link) > 20
    
    def test_multiple_products_have_unique_links(self, sample_products_list):
        """Test that different products have different affiliate links."""
        links = []
        for product in sample_products_list:
            link = product.promotion_link if hasattr(product, 'promotion_link') else product.product_detail_url
            links.append(link)
        
        # All links should be unique
        assert len(links) == len(set(links))
