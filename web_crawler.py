#!/usr/bin/env python3
"""
Web Crawler Module for Website to PDF Converter
Uses Scrapy to crawl websites with depth control and extract content and images
"""

import scrapy
import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
from datetime import datetime

class WebsiteCrawlerSpider(scrapy.Spider):
    """
    Scrapy spider for crawling websites with depth control
    """
    name = 'website_crawler'
    
    def __init__(self, start_url=None, max_depth=2, output_dir=None, *args, **kwargs):
        super(WebsiteCrawlerSpider, self).__init__(*args, **kwargs)
        
        if not start_url:
            raise ValueError("start_url is required")
        
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_depth = int(max_depth)
        self.output_dir = output_dir or '/tmp/crawler_output'
        self.base_domain = urlparse(start_url).netloc
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'images'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'pages'), exist_ok=True)
        
        # Initialize data storage
        self.crawled_pages = []
        self.downloaded_images = []
        self.failed_urls = []
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
    def start_requests(self):
        """Generate initial requests with depth tracking"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'depth': 0}
            )
    
    def parse(self, response):
        """Parse page content and extract links and images"""
        current_depth = response.meta.get('depth', 0)
        
        # Extract page content
        page_data = self.extract_page_content(response)
        self.crawled_pages.append(page_data)
        
        # Save page content to file
        self.save_page_content(page_data)
        
        # Extract and download images
        self.extract_and_download_images(response)
        
        # Follow links if within depth limit
        if current_depth < self.max_depth:
            for link in self.extract_links(response):
                yield scrapy.Request(
                    url=link,
                    callback=self.parse,
                    meta={'depth': current_depth + 1},
                    errback=self.handle_error
                )
    
    def extract_page_content(self, response):
        """Extract and clean page content"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'Untitled'
        
        # Extract main content
        main_content = self.extract_main_content(soup)
        
        # Extract metadata
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else ''
        
        # Extract headings structure
        headings = self.extract_headings(soup)
        
        page_data = {
            'url': response.url,
            'title': title_text,
            'description': description,
            'content': main_content,
            'headings': headings,
            'depth': response.meta.get('depth', 0),
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status
        }
        
        return page_data
    
    def extract_main_content(self, soup):
        """Extract main content from page, prioritizing content areas"""
        # Try to find main content areas
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '#content',
            '#main',
            '.post-content',
            '.entry-content',
            'div[role="main"]'
        ]
        
        main_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = elements[0]
                break
        
        # If no main content area found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Clean up the content
            text = main_content.get_text(separator=' ', strip=True)
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            return text
        
        return ''
    
    def extract_headings(self, soup):
        """Extract heading structure for document outline"""
        headings = []
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip(),
                    'id': heading.get('id', '')
                })
        return headings
    
    def extract_links(self, response):
        """Extract and filter links for crawling"""
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(response.url, href)
            
            # Filter links
            if self.should_follow_link(absolute_url):
                links.add(absolute_url)
        
        return list(links)
    
    def should_follow_link(self, url):
        """Determine if a link should be followed"""
        parsed_url = urlparse(url)
        
        # Only follow links within the same domain
        if parsed_url.netloc != self.base_domain:
            return False
        
        # Skip certain file types
        skip_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                          '.zip', '.rar', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov'}
        
        path = parsed_url.path.lower()
        if any(path.endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip fragments and query parameters for duplicate detection
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        return True
    
    def extract_and_download_images(self, response):
        """Extract and download images from the page"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
            
            # Convert relative URLs to absolute
            img_url = urljoin(response.url, src)
            
            # Download image
            try:
                self.download_image(img_url, response.url)
            except Exception as e:
                self.logger.error(f"Failed to download image {img_url}: {e}")
    
    def download_image(self, img_url, page_url):
        """Download an image and save it locally"""
        try:
            # Generate filename
            parsed_url = urlparse(img_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = f"image_{len(self.downloaded_images)}.jpg"
            
            # Ensure unique filename
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(self.output_dir, 'images', filename)):
                filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # Download image
            response = requests.get(img_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Save image
            img_path = os.path.join(self.output_dir, 'images', filename)
            with open(img_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Record image info
            img_info = {
                'url': img_url,
                'local_path': img_path,
                'filename': filename,
                'page_url': page_url,
                'size': os.path.getsize(img_path)
            }
            self.downloaded_images.append(img_info)
            
            self.logger.info(f"Downloaded image: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to download image {img_url}: {e}")
            self.failed_urls.append({'url': img_url, 'error': str(e), 'type': 'image'})
    
    def save_page_content(self, page_data):
        """Save page content to JSON file"""
        # Create safe filename from URL
        safe_name = re.sub(r'[^\w\-_.]', '_', page_data['url'].replace('https://', '').replace('http://', ''))
        filename = f"page_{len(self.crawled_pages)}_{safe_name[:50]}.json"
        
        filepath = os.path.join(self.output_dir, 'pages', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        self.failed_urls.append({
            'url': failure.request.url,
            'error': str(failure.value),
            'type': 'page'
        })
    
    def closed(self, reason):
        """Called when spider is closed"""
        # Save crawl summary
        summary = {
            'start_url': self.start_urls[0],
            'max_depth': self.max_depth,
            'pages_crawled': len(self.crawled_pages),
            'images_downloaded': len(self.downloaded_images),
            'failed_urls': len(self.failed_urls),
            'crawl_time': datetime.now().isoformat(),
            'reason': reason
        }
        
        summary_path = os.path.join(self.output_dir, 'crawl_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Crawl completed: {summary}")


class WebCrawler:
    """
    Main web crawler class that manages the Scrapy spider
    """
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or '/tmp/crawler_output'
    
    def crawl_website(self, start_url, max_depth=2):
        """
        Crawl a website with specified depth limit
        
        Args:
            start_url (str): Starting URL to crawl
            max_depth (int): Maximum depth to crawl (0 = only start page)
        
        Returns:
            dict: Crawl results summary
        """
        # Configure Scrapy settings
        settings = get_project_settings()
        settings.update({
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_DELAY': 1,  # Be respectful to servers
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'CONCURRENT_REQUESTS': 8,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
            'USER_AGENT': 'Website-to-PDF-Converter (+https://example.com/bot)',
            'LOG_LEVEL': 'INFO',
            'DEPTH_LIMIT': max_depth,
            'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        })
        
        # Create and run crawler process
        process = CrawlerProcess(settings)
        process.crawl(
            WebsiteCrawlerSpider,
            start_url=start_url,
            max_depth=max_depth,
            output_dir=self.output_dir
        )
        process.start()
        
        # Load and return summary
        summary_path = os.path.join(self.output_dir, 'crawl_summary.json')
        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {'error': 'Crawl summary not found'}


def main():
    """Test the web crawler"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python web_crawler.py <start_url> [max_depth]")
        sys.exit(1)
    
    start_url = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    crawler = WebCrawler('/tmp/test_crawl')
    result = crawler.crawl_website(start_url, max_depth)
    print(f"Crawl result: {result}")


if __name__ == "__main__":
    main()

