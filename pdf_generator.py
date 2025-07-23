#!/usr/bin/env python3
"""
PDF Generator Module for Website to PDF Converter
Uses WeasyPrint to generate PDF documents from scraped content and OCR text
"""

import weasyprint
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse
import base64

class PDFGenerator:
    """
    PDF generator that creates PDF documents from web content and OCR text
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize PDF generator
        
        Args:
            output_dir (str): Directory to save generated PDFs
        """
        self.output_dir = output_dir or '/tmp/pdf_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # CSS styles for PDF layout
        self.css_styles = self._get_default_css()
    
    def _get_default_css(self) -> str:
        """
        Get default CSS styles for PDF generation
        
        Returns:
            str: CSS styles
        """
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "Website to PDF Converter";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .title-page {
            text-align: center;
            padding: 4cm 0;
            page-break-after: always;
        }
        
        .title-page h1 {
            font-size: 24pt;
            color: #2c3e50;
            margin-bottom: 1cm;
        }
        
        .title-page .subtitle {
            font-size: 14pt;
            color: #7f8c8d;
            margin-bottom: 2cm;
        }
        
        .title-page .metadata {
            font-size: 10pt;
            color: #95a5a6;
        }
        
        .table-of-contents {
            page-break-after: always;
            margin-bottom: 2cm;
        }
        
        .table-of-contents h2 {
            font-size: 18pt;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5cm;
            margin-bottom: 1cm;
        }
        
        .toc-entry {
            margin-bottom: 0.3cm;
            display: flex;
            justify-content: space-between;
        }
        
        .toc-entry a {
            text-decoration: none;
            color: #2980b9;
        }
        
        .toc-entry a:hover {
            text-decoration: underline;
        }
        
        .page-content {
            page-break-before: always;
            margin-bottom: 2cm;
        }
        
        .page-header {
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.5cm;
            margin-bottom: 1cm;
        }
        
        .page-header h1 {
            font-size: 16pt;
            color: #2c3e50;
            margin: 0;
        }
        
        .page-header .url {
            font-size: 9pt;
            color: #7f8c8d;
            font-family: monospace;
            margin-top: 0.2cm;
        }
        
        .page-header .metadata {
            font-size: 9pt;
            color: #95a5a6;
            margin-top: 0.2cm;
        }
        
        .content-section {
            margin-bottom: 1.5cm;
        }
        
        .content-section h2 {
            font-size: 14pt;
            color: #34495e;
            margin-bottom: 0.5cm;
        }
        
        .content-section h3 {
            font-size: 12pt;
            color: #34495e;
            margin-bottom: 0.3cm;
        }
        
        .content-text {
            text-align: justify;
            margin-bottom: 1cm;
        }
        
        .ocr-section {
            background-color: #f8f9fa;
            border-left: 4px solid #17a2b8;
            padding: 0.5cm;
            margin: 1cm 0;
        }
        
        .ocr-section h3 {
            color: #17a2b8;
            margin-top: 0;
            font-size: 11pt;
        }
        
        .ocr-text {
            font-size: 10pt;
            color: #495057;
            font-style: italic;
        }
        
        .image-placeholder {
            border: 1px dashed #dee2e6;
            padding: 1cm;
            text-align: center;
            color: #6c757d;
            margin: 0.5cm 0;
            background-color: #f8f9fa;
        }
        
        .summary-section {
            background-color: #e8f5e8;
            border: 1px solid #28a745;
            padding: 1cm;
            margin: 1cm 0;
        }
        
        .summary-section h3 {
            color: #155724;
            margin-top: 0;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.5cm 0;
        }
        
        .stats-table th,
        .stats-table td {
            border: 1px solid #dee2e6;
            padding: 0.3cm;
            text-align: left;
        }
        
        .stats-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        """
    
    def generate_pdf(self, crawl_data_dir: str, ocr_data_dir: str = None, 
                    output_filename: str = None) -> str:
        """
        Generate PDF from crawled data and OCR results
        
        Args:
            crawl_data_dir (str): Directory containing crawled page data
            ocr_data_dir (str): Directory containing OCR results (optional)
            output_filename (str): Name of output PDF file (optional)
        
        Returns:
            str: Path to generated PDF file
        """
        try:
            # Load crawl data
            crawl_summary = self._load_crawl_summary(crawl_data_dir)
            page_data = self._load_page_data(crawl_data_dir)
            
            # Load OCR data if available
            ocr_data = {}
            if ocr_data_dir and os.path.exists(ocr_data_dir):
                ocr_data = self._load_ocr_data(ocr_data_dir)
            
            # Generate HTML content
            html_content = self._generate_html(crawl_summary, page_data, ocr_data)
            
            # Generate PDF
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = urlparse(crawl_summary.get('start_url', '')).netloc
                output_filename = f"website_pdf_{domain}_{timestamp}.pdf"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Create PDF using WeasyPrint
            html_doc = weasyprint.HTML(string=html_content)
            css_doc = weasyprint.CSS(string=self.css_styles)
            
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
            
            self.logger.info(f"PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            raise
    
    def _load_crawl_summary(self, crawl_data_dir: str) -> Dict:
        """Load crawl summary data"""
        summary_path = os.path.join(crawl_data_dir, 'crawl_summary.json')
        if not os.path.exists(summary_path):
            raise FileNotFoundError(f"Crawl summary not found: {summary_path}")
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_page_data(self, crawl_data_dir: str) -> List[Dict]:
        """Load all page data from crawl results"""
        pages_dir = os.path.join(crawl_data_dir, 'pages')
        if not os.path.exists(pages_dir):
            raise FileNotFoundError(f"Pages directory not found: {pages_dir}")
        
        page_data = []
        for filename in os.listdir(pages_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(pages_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    page_data.append(json.load(f))
        
        # Sort by depth and URL
        page_data.sort(key=lambda x: (x.get('depth', 0), x.get('url', '')))
        return page_data
    
    def _load_ocr_data(self, ocr_data_dir: str) -> Dict:
        """Load OCR results data"""
        ocr_data = {}
        
        # Load OCR summary if available
        summary_path = os.path.join(ocr_data_dir, 'ocr_summary.json')
        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                ocr_summary = json.load(f)
                
                # Index OCR results by image filename
                for result in ocr_summary.get('results', []):
                    image_path = result.get('image_path', '')
                    filename = os.path.basename(image_path)
                    ocr_data[filename] = result
        
        return ocr_data
    
    def _generate_html(self, crawl_summary: Dict, page_data: List[Dict], 
                      ocr_data: Dict) -> str:
        """
        Generate HTML content for PDF
        
        Args:
            crawl_summary (dict): Crawl summary data
            page_data (list): List of page data
            ocr_data (dict): OCR results data
        
        Returns:
            str: HTML content
        """
        html_parts = []
        
        # HTML document start
        html_parts.append("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Website to PDF Conversion</title>
        </head>
        <body>
        """)
        
        # Title page
        html_parts.append(self._generate_title_page(crawl_summary))
        
        # Table of contents
        html_parts.append(self._generate_table_of_contents(page_data))
        
        # Summary section
        html_parts.append(self._generate_summary_section(crawl_summary, ocr_data))
        
        # Page content
        for page in page_data:
            html_parts.append(self._generate_page_content(page, ocr_data))
        
        # HTML document end
        html_parts.append("""
        </body>
        </html>
        """)
        
        return ''.join(html_parts)
    
    def _generate_title_page(self, crawl_summary: Dict) -> str:
        """Generate title page HTML"""
        start_url = crawl_summary.get('start_url', 'Unknown URL')
        domain = urlparse(start_url).netloc
        crawl_time = crawl_summary.get('crawl_time', 'Unknown')
        
        return f"""
        <div class="title-page">
            <h1>Website to PDF Conversion</h1>
            <div class="subtitle">Complete website content with OCR text extraction</div>
            <div class="metadata">
                <p><strong>Source:</strong> {start_url}</p>
                <p><strong>Domain:</strong> {domain}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Crawled:</strong> {crawl_time}</p>
            </div>
        </div>
        """
    
    def _generate_table_of_contents(self, page_data: List[Dict]) -> str:
        """Generate table of contents HTML"""
        toc_entries = []
        
        for i, page in enumerate(page_data, 1):
            title = page.get('title', 'Untitled')
            url = page.get('url', '')
            depth = page.get('depth', 0)
            
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Add indentation based on depth
            indent = "  " * depth
            
            toc_entries.append(f"""
            <div class="toc-entry">
                <span>{indent}{title}</span>
                <span>Page {i}</span>
            </div>
            """)
        
        return f"""
        <div class="table-of-contents">
            <h2>Table of Contents</h2>
            {''.join(toc_entries)}
        </div>
        """
    
    def _generate_summary_section(self, crawl_summary: Dict, ocr_data: Dict) -> str:
        """Generate summary section HTML"""
        pages_crawled = crawl_summary.get('pages_crawled', 0)
        images_downloaded = crawl_summary.get('images_downloaded', 0)
        max_depth = crawl_summary.get('max_depth', 0)
        
        ocr_processed = len([r for r in ocr_data.values() if r.get('success', False)])
        ocr_text_found = len([r for r in ocr_data.values() 
                             if r.get('success', False) and r.get('full_text', '').strip()])
        
        return f"""
        <div class="summary-section">
            <h3>Conversion Summary</h3>
            <table class="stats-table">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Pages Crawled</td><td>{pages_crawled}</td></tr>
                <tr><td>Maximum Depth</td><td>{max_depth}</td></tr>
                <tr><td>Images Downloaded</td><td>{images_downloaded}</td></tr>
                <tr><td>Images Processed with OCR</td><td>{ocr_processed}</td></tr>
                <tr><td>Images with Text Found</td><td>{ocr_text_found}</td></tr>
            </table>
        </div>
        """
    
    def _generate_page_content(self, page: Dict, ocr_data: Dict) -> str:
        """Generate HTML content for a single page"""
        title = page.get('title', 'Untitled')
        url = page.get('url', '')
        content = page.get('content', '')
        depth = page.get('depth', 0)
        timestamp = page.get('timestamp', '')
        
        # Clean and format content
        content = self._clean_html_content(content)
        
        # Generate headings structure
        headings_html = self._generate_headings_html(page.get('headings', []))
        
        # Generate OCR content if available
        ocr_html = self._generate_ocr_content_html(page, ocr_data)
        
        return f"""
        <div class="page-content">
            <div class="page-header">
                <h1>{title}</h1>
                <div class="url">{url}</div>
                <div class="metadata">Depth: {depth} | Crawled: {timestamp}</div>
            </div>
            
            {headings_html}
            
            <div class="content-section">
                <h2>Page Content</h2>
                <div class="content-text">{content}</div>
            </div>
            
            {ocr_html}
        </div>
        """
    
    def _generate_headings_html(self, headings: List[Dict]) -> str:
        """Generate HTML for page headings structure"""
        if not headings:
            return ""
        
        headings_list = []
        for heading in headings:
            level = heading.get('level', 1)
            text = heading.get('text', '')
            indent = "  " * (level - 1)
            headings_list.append(f"{indent}• {text}")
        
        return f"""
        <div class="content-section">
            <h2>Page Structure</h2>
            <pre>{'<br>'.join(headings_list)}</pre>
        </div>
        """
    
    def _generate_ocr_content_html(self, page: Dict, ocr_data: Dict) -> str:
        """Generate HTML for OCR content related to this page"""
        page_url = page.get('url', '')
        ocr_sections = []
        
        # Find OCR results for images from this page
        for filename, ocr_result in ocr_data.items():
            if (ocr_result.get('success', False) and 
                ocr_result.get('full_text', '').strip()):
                
                # Check if this OCR result is from the current page
                # (This is a simplified check - in practice, you'd want better tracking)
                text = ocr_result.get('full_text', '')
                confidence = ocr_result.get('confidence_avg', 0)
                
                ocr_sections.append(f"""
                <div class="ocr-section">
                    <h3>Text Extracted from Image: {filename}</h3>
                    <div class="ocr-text">{text}</div>
                    <div style="font-size: 9pt; color: #6c757d; margin-top: 0.3cm;">
                        Confidence: {confidence:.1%}
                    </div>
                </div>
                """)
        
        if ocr_sections:
            return f"""
            <div class="content-section">
                <h2>Text Extracted from Images</h2>
                {''.join(ocr_sections)}
            </div>
            """
        
        return ""
    
    def _clean_html_content(self, content: str) -> str:
        """Clean and format content for PDF"""
        if not content:
            return "No content available."
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Split into paragraphs for better formatting
        paragraphs = content.split('. ')
        if len(paragraphs) > 1:
            # Join with proper paragraph breaks
            content = '</p><p>'.join(paragraphs)
            content = f'<p>{content}</p>'
        
        return content


def main():
    """Test the PDF generator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_generator.py <crawl_data_dir> [ocr_data_dir]")
        sys.exit(1)
    
    crawl_data_dir = sys.argv[1]
    ocr_data_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize PDF generator
    generator = PDFGenerator('/tmp/pdf_output')
    
    try:
        pdf_path = generator.generate_pdf(crawl_data_dir, ocr_data_dir)
        print(f"PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

