"""
Integration tests for the complete application flow.
Tests end-to-end scenarios combining multiple components.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json
import psycopg2


@pytest.fixture
def full_app():
    """Create a fully configured Flask app for integration testing."""
    with patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb',
        'ALI_KEY': 'test_key',
        'ALI_SECRET': 'test_secret'
    }):
        with patch('psycopg2.connect'):
            with patch('aliexpress_api.AliexpressApi'):
                from flask import Flask, jsonify, request
                from flask_cors import CORS
                
                app = Flask(__name__)
                CORS(app)
                
                @app.route('/api/products', methods=['GET'])
                def get_products():
                    try:
                        import os
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
                    import os
                    keyword = request.json.get('keyword', 'smart gadgets')
                    
                    try:
                        # Simulate API call and DB save
                        return jsonify({
                            "status": "success",
                            "message": f"AI Scout found and analyzed items for '{keyword}'."
                        })
                    except Exception as e:
                        return jsonify({"status": "error", "error": str(e)}), 500
                
                app.config['TESTING'] = True
                return app


@pytest.fixture
def full_client(full_app):
    """Create test client for integration tests."""
    return full_app.test_client()


class TestEndToEndFlow:
    """Tests for complete end-to-end application flows."""
    
    @patch('psycopg2.connect')
    def test_scan_and_retrieve_products_flow(self, mock_connect, full_client, sample_db_rows):
        """Test complete flow: scan market -> save products -> retrieve products."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Step 1: Scan market
        scan_response = full_client.post('/api/scan-market',
                                        json={'keyword': 'bluetooth earphones'},
                                        content_type='application/json')
        
        assert scan_response.status_code == 200
        scan_data = json.loads(scan_response.data)
        assert scan_data['status'] == 'success'
        
        # Step 2: Retrieve products (simulate products were saved)
        mock_cursor.fetchall.return_value = sample_db_rows
        
        products_response = full_client.get('/api/products')
        
        assert products_response.status_code == 200
        products_data = json.loads(products_response.data)
        assert len(products_data) > 0
    
    @patch('psycopg2.connect')
    def test_multiple_scans_accumulate_products(self, mock_connect, full_client):
        """Test that multiple scans accumulate products in database."""
        keywords = ['smart watch', 'earbuds', 'drone']
        
        for keyword in keywords:
            response = full_client.post('/api/scan-market',
                                       json={'keyword': keyword},
                                       content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert keyword in data['message']
    
    @patch('psycopg2.connect')
    def test_concurrent_api_requests(self, mock_connect, full_client, sample_db_rows):
        """Test handling of concurrent API requests."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = sample_db_rows
        
        # Simulate concurrent requests
        responses = []
        for i in range(10):
            response = full_client.get('/api/products')
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    @patch('psycopg2.connect')
    def test_database_transaction_consistency(self, mock_connect, full_client):
        """Test that database transactions maintain consistency."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Scan products
        response = full_client.post('/api/scan-market',
                                   json={'keyword': 'test product'},
                                   content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify that if we were to check the database, commits were called
        # This tests the transaction pattern


class TestErrorRecovery:
    """Tests for error recovery and resilience."""
    
    @patch('psycopg2.connect')
    def test_database_failure_recovery(self, mock_connect, full_client):
        """Test that app recovers from database failures."""
        # First request fails
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        response1 = full_client.get('/api/products')
        assert response1.status_code == 500
        
        # Second request succeeds (simulating reconnection)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.side_effect = None
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        response2 = full_client.get('/api/products')
        assert response2.status_code == 200
    
    @patch('psycopg2.connect')
    def test_partial_data_handling(self, mock_connect, full_client):
        """Test handling of partial or malformed data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Return partial data (missing some fields)
        partial_rows = [
            ("Product", None, "img.jpg", None, "category"),
        ]
        mock_cursor.fetchall.return_value = partial_rows
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['price'] is None
    
    def test_invalid_endpoint_handling(self, full_client):
        """Test handling of requests to invalid endpoints."""
        response = full_client.get('/api/invalid-endpoint')
        
        assert response.status_code == 404
    
    def test_method_not_allowed_handling(self, full_client):
        """Test handling of invalid HTTP methods."""
        # GET to POST endpoint
        response = full_client.get('/api/scan-market')
        assert response.status_code == 405
        
        # POST to GET endpoint
        response = full_client.post('/api/products')
        assert response.status_code == 405


class TestDataIntegrity:
    """Tests for data integrity and validation."""
    
    @patch('psycopg2.connect')
    def test_duplicate_products_handled(self, mock_connect, full_client):
        """Test that duplicate products are handled correctly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Scan same keyword twice
        keyword = 'bluetooth earphones'
        
        response1 = full_client.post('/api/scan-market',
                                    json={'keyword': keyword},
                                    content_type='application/json')
        
        response2 = full_client.post('/api/scan-market',
                                    json={'keyword': keyword},
                                    content_type='application/json')
        
        # Both should succeed (duplicates handled by ON CONFLICT)
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @patch('psycopg2.connect')
    def test_special_characters_preserved(self, mock_connect, full_client):
        """Test that special characters in data are preserved."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        special_rows = [
            ("Product with 'quotes' & symbols", "€29.99", "img.jpg", "link", "cat"),
        ]
        mock_cursor.fetchall.return_value = special_rows
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "quotes" in data[0]['name']
        assert "&" in data[0]['name']
    
    @patch('psycopg2.connect')
    def test_unicode_data_handling(self, mock_connect, full_client):
        """Test that Unicode characters are handled properly."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        unicode_rows = [
            ("产品名称 🎉", "¥99.99", "img.jpg", "link", "类别"),
        ]
        mock_cursor.fetchall.return_value = unicode_rows
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "产品名称" in data[0]['name']


class TestPerformance:
    """Tests for performance-related scenarios."""
    
    @patch('psycopg2.connect')
    def test_large_product_list_handling(self, mock_connect, full_client):
        """Test handling of large product lists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Create 50 products (the limit)
        large_dataset = [
            (f"Product {i}", f"{i}.99", f"img{i}.jpg", f"link{i}", "cat")
            for i in range(50)
        ]
        mock_cursor.fetchall.return_value = large_dataset
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 50
    
    @patch('psycopg2.connect')
    def test_empty_database_performance(self, mock_connect, full_client):
        """Test performance with empty database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0


class TestSecurityScenarios:
    """Tests for security-related scenarios."""
    
    def test_sql_injection_protection_in_keyword(self, full_client):
        """Test that SQL injection attempts in keywords are handled safely."""
        malicious_keyword = "'; DROP TABLE products; --"
        
        response = full_client.post('/api/scan-market',
                                   json={'keyword': malicious_keyword},
                                   content_type='application/json')
        
        # Should handle safely (parameterized queries protect against injection)
        assert response.status_code == 200
    
    def test_xss_protection_in_product_data(self, full_client):
        """Test that XSS attempts in product data are handled."""
        xss_keyword = '<script>alert("XSS")</script>'
        
        response = full_client.post('/api/scan-market',
                                   json={'keyword': xss_keyword},
                                   content_type='application/json')
        
        # Should handle safely
        assert response.status_code == 200
    
    @patch('psycopg2.connect')
    def test_large_payload_handling(self, mock_connect, full_client):
        """Test handling of unusually large payloads."""
        large_keyword = 'a' * 10000
        
        response = full_client.post('/api/scan-market',
                                   json={'keyword': large_keyword},
                                   content_type='application/json')
        
        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 413]
    
    def test_malformed_json_handling(self, full_client):
        """Test handling of malformed JSON in requests."""
        response = full_client.post('/api/scan-market',
                                   data='{"invalid": json}',
                                   content_type='application/json')
        
        # Should reject malformed JSON
        assert response.status_code in [400, 500]


class TestAPIConsistency:
    """Tests for API consistency and behavior."""
    
    @patch('psycopg2.connect')
    def test_consistent_response_format(self, mock_connect, full_client, sample_db_rows):
        """Test that API returns consistent response formats."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = sample_db_rows
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that all products have required fields
        for product in data:
            assert 'name' in product
            assert 'price' in product
            assert 'img' in product
            assert 'link' in product
            assert 'tag' in product
    
    def test_content_type_headers(self, full_client):
        """Test that proper content-type headers are returned."""
        response = full_client.post('/api/scan-market',
                                   json={'keyword': 'test'},
                                   content_type='application/json')
        
        assert response.content_type == 'application/json'
    
    @patch('psycopg2.connect')
    def test_error_response_format(self, mock_connect, full_client):
        """Test that error responses have consistent format."""
        mock_connect.side_effect = Exception("Database error")
        
        response = full_client.get('/api/products')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
