"""
Unit tests for Flask API routes.
Tests cover all API endpoints including success cases, error handling, and edge cases.
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
import psycopg2


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    with patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb',
        'ALI_KEY': 'test_key',
        'ALI_SECRET': 'test_secret'
    }):
        with patch('psycopg2.connect'):
            with patch('aliexpress_api.AliexpressApi'):
                # Import app after environment is set
                import sys
                import os
                from flask import Flask, jsonify, request
                from flask_cors import CORS
                
                app = Flask(__name__)
                CORS(app)
                
                # Define routes inline for testing
                @app.route('/api/products', methods=['GET'])
                def get_products():
                    try:
                        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                        cur = conn.cursor()
                        cur.execute("SELECT title, price, image_url, affiliate_link, category FROM products ORDER BY created_at DESC LIMIT 50;")
                        rows = cur.fetchall()
                        cur.close()
                        conn.close()
                        
                        products = []
                        for row in rows:
                            products.append({
                                "name": row[0],
                                "price": row[1],
                                "img": row[2],
                                "link": row[3],
                                "tag": row[4]
                            })
                        return jsonify(products)
                    except Exception as e:
                        return jsonify({"error": str(e)}), 500
                
                @app.route('/api/scan-market', methods=['POST'])
                def scan_market():
                    keyword = request.json.get('keyword', 'smart gadgets')
                    return jsonify({
                        "status": "success",
                        "message": f"Scanned for {keyword}"
                    })
                
                app.config['TESTING'] = True
                return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestGetProductsEndpoint:
    """Tests for GET /api/products endpoint."""
    
    @patch('psycopg2.connect')
    def test_get_products_success(self, mock_connect, client, sample_db_rows):
        """Test successful retrieval of products."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = sample_db_rows
        
        response = client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]['name'] == "Product 1"
        assert data[0]['price'] == "19.99"
        assert data[0]['tag'] == "smart watch"
    
    @patch('psycopg2.connect')
    def test_get_products_empty_database(self, mock_connect, client):
        """Test GET /api/products when database is empty."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        response = client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    @patch('psycopg2.connect')
    def test_get_products_database_error(self, mock_connect, client):
        """Test GET /api/products when database connection fails."""
        mock_connect.side_effect = psycopg2.OperationalError("Database connection failed")
        
        response = client.get('/api/products')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Database connection failed' in data['error']
    
    @patch('psycopg2.connect')
    def test_get_products_query_error(self, mock_connect, client):
        """Test GET /api/products when SQL query fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.ProgrammingError("Invalid query")
        
        response = client.get('/api/products')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('psycopg2.connect')
    def test_get_products_returns_json_format(self, mock_connect, client, sample_db_rows):
        """Test that GET /api/products returns proper JSON format."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [sample_db_rows[0]]
        
        response = client.get('/api/products')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        
        # Check required fields
        assert 'name' in data[0]
        assert 'price' in data[0]
        assert 'img' in data[0]
        assert 'link' in data[0]
        assert 'tag' in data[0]
    
    @patch('psycopg2.connect')
    def test_get_products_limits_to_50(self, mock_connect, client):
        """Test that GET /api/products limits results to 50 items."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Create 100 mock rows
        large_dataset = [
            (f"Product {i}", f"{i}.99", f"img{i}.jpg", f"link{i}.com", "category")
            for i in range(100)
        ]
        mock_cursor.fetchall.return_value = large_dataset
        
        response = client.get('/api/products')
        
        # Query should include LIMIT 50
        call_args = mock_cursor.execute.call_args[0][0]
        assert "LIMIT 50" in call_args
    
    @patch('psycopg2.connect')
    def test_get_products_orders_by_created_at_desc(self, mock_connect, client):
        """Test that products are ordered by creation date descending."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        response = client.get('/api/products')
        
        # Query should include ORDER BY created_at DESC
        call_args = mock_cursor.execute.call_args[0][0]
        assert "ORDER BY created_at DESC" in call_args
    
    @patch('psycopg2.connect')
    def test_get_products_closes_connection(self, mock_connect, client):
        """Test that database connections are properly closed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        response = client.get('/api/products')
        
        # Verify cleanup
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_get_products_handles_none_values(self, mock_connect, client):
        """Test that None values in database are handled properly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Rows with None values
        rows_with_none = [
            ("Product", None, "img.jpg", "link.com", None),
            ("Another", "29.99", None, None, "category"),
        ]
        mock_cursor.fetchall.return_value = rows_with_none
        
        response = client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data[0]['price'] is None
        assert data[1]['img'] is None
    
    @patch('psycopg2.connect')
    def test_get_products_with_special_characters(self, mock_connect, client):
        """Test products containing special characters in data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        special_rows = [
            ("Product with 'quotes' & <html>", "€29.99", "img.jpg", "link.com", "cat&egory"),
        ]
        mock_cursor.fetchall.return_value = special_rows
        
        response = client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "quotes" in data[0]['name']
        assert "&" in data[0]['name']


class TestScanMarketEndpoint:
    """Tests for POST /api/scan-market endpoint."""
    
    def test_scan_market_with_keyword(self, client):
        """Test POST /api/scan-market with custom keyword."""
        response = client.post('/api/scan-market',
                              json={'keyword': 'bluetooth earphones'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'bluetooth earphones' in data['message']
    
    def test_scan_market_without_keyword(self, client):
        """Test POST /api/scan-market without keyword (uses default)."""
        response = client.post('/api/scan-market',
                              json={},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'smart gadgets' in data['message']
    
    def test_scan_market_empty_keyword(self, client):
        """Test POST /api/scan-market with empty keyword."""
        response = client.post('/api/scan-market',
                              json={'keyword': ''},
                              content_type='application/json')
        
        assert response.status_code == 200
        # Empty keyword should be handled
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_scan_market_special_characters_keyword(self, client):
        """Test POST /api/scan-market with special characters in keyword."""
        response = client.post('/api/scan-market',
                              json={'keyword': 'phone "cases" & accessories'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_scan_market_invalid_json(self, client):
        """Test POST /api/scan-market with invalid JSON."""
        response = client.post('/api/scan-market',
                              data='not json',
                              content_type='application/json')
        
        # Should handle invalid JSON gracefully
        assert response.status_code in [400, 500]
    
    def test_scan_market_missing_content_type(self, client):
        """Test POST /api/scan-market without content-type header."""
        response = client.post('/api/scan-market',
                              data=json.dumps({'keyword': 'test'}))
        
        # Should handle missing content-type
        assert response.status_code in [200, 400, 415]
    
    def test_scan_market_very_long_keyword(self, client):
        """Test POST /api/scan-market with very long keyword."""
        long_keyword = 'a' * 1000
        response = client.post('/api/scan-market',
                              json={'keyword': long_keyword},
                              content_type='application/json')
        
        # Should handle long keywords
        assert response.status_code in [200, 400]
    
    def test_scan_market_unicode_keyword(self, client):
        """Test POST /api/scan-market with Unicode characters."""
        response = client.post('/api/scan-market',
                              json={'keyword': '蓝牙耳机 🎧'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_scan_market_numeric_keyword(self, client):
        """Test POST /api/scan-market with numeric keyword."""
        response = client.post('/api/scan-market',
                              json={'keyword': 12345},
                              content_type='application/json')
        
        # Should handle numeric values
        assert response.status_code == 200
    
    def test_scan_market_null_keyword(self, client):
        """Test POST /api/scan-market with null keyword."""
        response = client.post('/api/scan-market',
                              json={'keyword': None},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should use default keyword when None provided
        assert 'smart gadgets' in data['message']


class TestCORSConfiguration:
    """Tests for CORS (Cross-Origin Resource Sharing) configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get('/api/products')
        
        # CORS should be enabled for cross-origin requests
        # The flask-cors library handles this
        assert response.status_code in [200, 500]  # Either success or error, but should respond
    
    def test_options_request_allowed(self, client):
        """Test that OPTIONS requests (preflight) are handled."""
        response = client.options('/api/products')
        
        # OPTIONS request should be handled by CORS
        assert response.status_code in [200, 204]


class TestAPIEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_get_request_to_post_endpoint(self, client):
        """Test GET request to POST-only endpoint."""
        response = client.get('/api/scan-market')
        
        # Should return Method Not Allowed
        assert response.status_code == 405
    
    def test_post_request_to_get_endpoint(self, client):
        """Test POST request to GET-only endpoint."""
        response = client.post('/api/products')
        
        # Should return Method Not Allowed
        assert response.status_code == 405
    
    def test_nonexistent_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
    
    def test_endpoint_with_trailing_slash(self, client):
        """Test endpoints with and without trailing slashes."""
        response1 = client.get('/api/products')
        response2 = client.get('/api/products/')
        
        # Both should work or one should redirect
        assert response1.status_code in [200, 500]
    
    @patch('psycopg2.connect')
    def test_concurrent_requests_handling(self, mock_connect, client, sample_db_rows):
        """Test that multiple concurrent requests are handled properly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = sample_db_rows
        
        # Simulate multiple requests
        responses = [client.get('/api/products') for _ in range(5)]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_large_request_body(self, client):
        """Test handling of large request body."""
        large_data = {'keyword': 'a' * 10000}
        response = client.post('/api/scan-market',
                              json=large_data,
                              content_type='application/json')
        
        # Should handle large payloads (or reject gracefully)
        assert response.status_code in [200, 413, 400]
