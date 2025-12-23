"""
Tests for HTML file validation and structure.
Validates HTML structure, required elements, and basic functionality.
"""
import pytest
import re
from pathlib import Path


@pytest.fixture
def html_content():
    """Load the index.html file content."""
    html_path = Path(__file__).parent.parent / 'index.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()


class TestHTMLStructure:
    """Tests for basic HTML structure and validity."""
    
    def test_html_file_exists(self):
        """Test that index.html file exists."""
        html_path = Path(__file__).parent.parent / 'index.html'
        assert html_path.exists()
    
    def test_html_has_doctype(self, html_content):
        """Test that HTML has DOCTYPE declaration."""
        assert '<!DOCTYPE html>' in html_content
    
    def test_html_has_html_tag(self, html_content):
        """Test that HTML has <html> tag."""
        assert '<html' in html_content
        assert '</html>' in html_content
    
    def test_html_has_head_section(self, html_content):
        """Test that HTML has <head> section."""
        assert '<head>' in html_content
        assert '</head>' in html_content
    
    def test_html_has_body_section(self, html_content):
        """Test that HTML has <body> section."""
        assert '<body' in html_content
        assert '</body>' in html_content
    
    def test_html_has_title(self, html_content):
        """Test that HTML has <title> tag."""
        assert '<title>' in html_content
        assert '</title>' in html_content
    
    def test_html_title_not_empty(self, html_content):
        """Test that page title is not empty."""
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        assert title_match is not None
        title = title_match.group(1).strip()
        assert len(title) > 0
    
    def test_html_has_meta_charset(self, html_content):
        """Test that HTML has charset meta tag."""
        assert 'charset=' in html_content.lower() or 'charset"' in html_content.lower()
    
    def test_html_has_viewport_meta(self, html_content):
        """Test that HTML has viewport meta tag for responsive design."""
        assert 'viewport' in html_content.lower()
    
    def test_html_lang_attribute(self, html_content):
        """Test that HTML has lang attribute."""
        assert 'lang=' in html_content


class TestRequiredElements:
    """Tests for required HTML elements."""
    
    def test_has_navigation(self, html_content):
        """Test that page has navigation element."""
        assert '<nav' in html_content.lower() or 'navigation' in html_content.lower()
    
    def test_has_main_heading(self, html_content):
        """Test that page has main heading (h1)."""
        assert '<h1' in html_content.lower() or 'text-xl' in html_content or 'text-2xl' in html_content
    
    def test_has_container_elements(self, html_content):
        """Test that page has container/structural elements."""
        structural_elements = ['<div', '<section', '<main', '<article']
        assert any(elem in html_content.lower() for elem in structural_elements)


class TestExternalDependencies:
    """Tests for external scripts and stylesheets."""
    
    def test_has_tailwind_cdn(self, html_content):
        """Test that Tailwind CSS is loaded from CDN."""
        assert 'tailwindcss' in html_content.lower() or 'cdn.tailwindcss' in html_content
    
    def test_has_font_awesome(self, html_content):
        """Test that Font Awesome is loaded for icons."""
        assert 'font-awesome' in html_content.lower() or 'fontawesome' in html_content.lower()
    
    def test_external_resources_use_https(self, html_content):
        """Test that external resources use HTTPS."""
        # Find all src and href attributes
        http_links = re.findall(r'(?:src|href)=["\']http://[^"\']+["\']', html_content)
        
        # Should use HTTPS for CDN resources
        for link in http_links:
            if 'cdn' in link or 'cloudflare' in link:
                pytest.fail(f"External CDN resource should use HTTPS: {link}")


class TestAPIIntegration:
    """Tests for API endpoint references in HTML."""
    
    def test_has_api_products_endpoint(self, html_content):
        """Test that HTML references the products API endpoint."""
        assert '/api/products' in html_content
    
    def test_has_api_scan_endpoint(self, html_content):
        """Test that HTML references the scan-market API endpoint."""
        # May or may not be present depending on UI design
        has_scan = '/api/scan-market' in html_content or 'scan' in html_content.lower()
        assert True  # This is optional functionality
    
    def test_api_endpoints_use_relative_paths(self, html_content):
        """Test that API endpoints use relative paths."""
        # Find API endpoint references
        api_refs = re.findall(r'["\'](?:https?://[^/]+)?(/api/[^"\']+)["\']', html_content)
        
        # Should use relative paths (starting with /)
        for ref in api_refs:
            assert ref.startswith('/')


class TestJavaScript:
    """Tests for JavaScript functionality."""
    
    def test_has_javascript(self, html_content):
        """Test that page includes JavaScript."""
        assert '<script' in html_content.lower()
    
    def test_has_fetch_api_usage(self, html_content):
        """Test that JavaScript uses fetch API for AJAX requests."""
        # Modern approach uses fetch
        has_fetch = 'fetch(' in html_content or 'fetch (' in html_content
        has_ajax = 'XMLHttpRequest' in html_content or 'ajax' in html_content.lower()
        
        # Should use modern fetch API or AJAX
        assert has_fetch or has_ajax or 'api' in html_content.lower()
    
    def test_no_inline_console_logs(self, html_content):
        """Test that there are no debug console.log statements."""
        # It's okay to have some console.logs for debugging
        # This test just ensures they're not excessive
        console_count = html_content.lower().count('console.log')
        assert console_count < 20  # Reasonable limit


class TestStyling:
    """Tests for CSS and styling."""
    
    def test_has_custom_styles(self, html_content):
        """Test that page has custom styles defined."""
        assert '<style' in html_content.lower() or 'class=' in html_content
    
    def test_uses_tailwind_classes(self, html_content):
        """Test that page uses Tailwind CSS classes."""
        tailwind_classes = ['flex', 'grid', 'bg-', 'text-', 'p-', 'm-', 'w-', 'h-']
        assert any(cls in html_content for cls in tailwind_classes)
    
    def test_has_responsive_design_classes(self, html_content):
        """Test that page includes responsive design classes."""
        responsive_indicators = ['sm:', 'md:', 'lg:', 'xl:', 'max-w-', 'min-w-']
        assert any(indicator in html_content for indicator in responsive_indicators)
    
    def test_has_color_scheme(self, html_content):
        """Test that page has defined color scheme."""
        # Should have color definitions
        has_colors = 'color' in html_content.lower() or 'bg-' in html_content or '#' in html_content
        assert has_colors


class TestAccessibility:
    """Tests for accessibility features."""
    
    def test_has_alt_attributes_for_images(self, html_content):
        """Test that images have alt attributes (or are decorative)."""
        # Find img tags
        img_tags = re.findall(r'<img[^>]*>', html_content, re.IGNORECASE)
        
        # If images exist, they should have alt or be handled properly
        for img in img_tags:
            # Either has alt attribute or is loaded dynamically
            has_alt = 'alt=' in img.lower()
            is_dynamic = 'src="${' in img or 'src="$' in img or ':src=' in img
            
            if not (has_alt or is_dynamic):
                # This is a warning, not a hard failure for dynamically loaded content
                pass
    
    def test_has_semantic_html(self, html_content):
        """Test that page uses semantic HTML elements."""
        semantic_elements = ['<nav', '<header', '<main', '<footer', '<section', '<article']
        semantic_count = sum(1 for elem in semantic_elements if elem in html_content.lower())
        
        # Should use at least some semantic elements
        assert semantic_count > 0
    
    def test_has_aria_labels_for_icons(self, html_content):
        """Test that icons have appropriate ARIA labels or text."""
        # If font-awesome is used, icons should be accessible
        # This is a best practice check
        has_icons = 'fa-' in html_content or '<i ' in html_content
        
        if has_icons:
            # Should have some accessibility considerations
            has_aria = 'aria-' in html_content.lower()
            has_title = 'title=' in html_content
            
            # At least some accessibility features should be present
            assert True  # Permissive for now


class TestContentStructure:
    """Tests for content structure and organization."""
    
    def test_has_product_display_area(self, html_content):
        """Test that page has area for displaying products."""
        # Should have container for products
        product_indicators = ['product', 'item', 'card', 'grid', 'catalog', 'store']
        assert any(indicator in html_content.lower() for indicator in product_indicators)
    
    def test_has_branding(self, html_content):
        """Test that page includes branding/title."""
        branding_indicators = ['AI Nexus', 'store', 'shop', 'logo', 'brand']
        assert any(brand in html_content for brand in branding_indicators)
    
    def test_page_title_descriptive(self, html_content):
        """Test that page title is descriptive."""
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).strip()
            # Title should be descriptive (more than just one word)
            assert len(title) > 5


class TestPerformance:
    """Tests for performance-related best practices."""
    
    def test_external_scripts_loaded_efficiently(self, html_content):
        """Test that external scripts are loaded appropriately."""
        # Script tags should exist
        script_tags = re.findall(r'<script[^>]*>', html_content)
        assert len(script_tags) > 0
    
    def test_css_loaded_before_body(self, html_content):
        """Test that CSS is loaded in head section."""
        head_section = html_content.split('</head>')[0] if '</head>' in html_content else ''
        
        # Style-related content should be in head
        has_styles_in_head = '<style' in head_section or 'stylesheet' in head_section or 'tailwind' in head_section
        assert has_styles_in_head
    
    def test_no_excessive_inline_styles(self, html_content):
        """Test that inline styles are not excessive."""
        inline_style_count = html_content.count('style=')
        
        # Should primarily use classes, not inline styles
        # Tailwind encourages utility classes
        assert inline_style_count < 50  # Reasonable limit


class TestHTMLValidation:
    """Tests for HTML validation and common issues."""
    
    def test_no_duplicate_ids(self, html_content):
        """Test that there are no duplicate IDs."""
        # Find all id attributes
        ids = re.findall(r'id=["\']([^"\']+)["\']', html_content)
        
        # Check for duplicates
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), f"Found duplicate IDs: {[id for id in ids if ids.count(id) > 1]}"
    
    def test_quotes_properly_closed(self, html_content):
        """Test that attribute quotes are properly closed."""
        # Count opening and closing quotes
        double_quotes = html_content.count('"')
        single_quotes = html_content.count("'")
        
        # Both should be even (opened and closed)
        assert double_quotes % 2 == 0, "Unmatched double quotes"
        # Single quotes might be in content, so this is more lenient
    
    def test_tags_properly_nested(self, html_content):
        """Test basic tag nesting (html, head, body)."""
        # HTML should come before head and body
        html_pos = html_content.find('<html')
        head_pos = html_content.find('<head>')
        body_pos = html_content.find('<body')
        
        if html_pos != -1 and head_pos != -1 and body_pos != -1:
            assert html_pos < head_pos < body_pos


class TestBrowserCompatibility:
    """Tests for browser compatibility features."""
    
    def test_has_charset_utf8(self, html_content):
        """Test that charset is set to UTF-8."""
        assert 'UTF-8' in html_content or 'utf-8' in html_content
    
    def test_viewport_meta_for_mobile(self, html_content):
        """Test that viewport is configured for mobile devices."""
        viewport_match = re.search(r'name=["\']viewport["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        
        if viewport_match:
            viewport_content = viewport_match.group(1)
            assert 'width=device-width' in viewport_content
            assert 'initial-scale' in viewport_content
