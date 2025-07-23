#!/usr/bin/env python3
"""
Converter routes for Website to PDF Flask application
"""

import os
import tempfile
import threading
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from src.web_crawler import WebCrawler
from src.pdf_generator import PDFGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

converter_bp = Blueprint('converter', __name__)

# Global dictionary to track conversion jobs
conversion_jobs = {}

class ConversionJob:
    """Class to track conversion job status"""
    def __init__(self, job_id, url, max_depth):
        self.job_id = job_id
        self.url = url
        self.max_depth = max_depth
        self.status = 'starting'
        self.progress = 0
        self.message = 'Initializing conversion...'
        self.error = None
        self.pdf_path = None
        self.created_at = datetime.now()
        self.temp_dir = tempfile.mkdtemp(prefix=f'conversion_{job_id}_')
    
    def update_status(self, status, progress=None, message=None, error=None):
        """Update job status"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if message is not None:
            self.message = message
        if error is not None:
            self.error = error
        logger.info(f"Job {self.job_id}: {status} - {message}")

@converter_bp.route('/convert', methods=['POST'])
def start_conversion():
    """Start a new website to PDF conversion"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url', '').strip()
        max_depth = data.get('max_depth', 2)
        
        # Validate input
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            max_depth = int(max_depth)
            if max_depth < 0 or max_depth > 5:
                return jsonify({'error': 'Max depth must be between 0 and 5'}), 400
        except ValueError:
            return jsonify({'error': 'Max depth must be a valid number'}), 400
        
        # Create new job
        job_id = str(uuid.uuid4())
        job = ConversionJob(job_id, url, max_depth)
        conversion_jobs[job_id] = job
        
        # Start conversion in background thread
        thread = threading.Thread(target=run_conversion, args=(job,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Conversion started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting conversion: {e}")
        return jsonify({'error': 'Failed to start conversion'}), 500

@converter_bp.route('/status/<job_id>', methods=['GET'])
def get_conversion_status(job_id):
    """Get the status of a conversion job"""
    job = conversion_jobs.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    response = {
        'job_id': job_id,
        'status': job.status,
        'progress': job.progress,
        'message': job.message,
        'url': job.url,
        'max_depth': job.max_depth,
        'created_at': job.created_at.isoformat()
    }
    
    if job.error:
        response['error'] = job.error
    
    return jsonify(response)

@converter_bp.route('/download/<job_id>', methods=['GET'])
def download_pdf(job_id):
    """Download the generated PDF"""
    job = conversion_jobs.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != 'completed':
        return jsonify({'error': 'Conversion not completed yet'}), 400
    
    if not job.pdf_path or not os.path.exists(job.pdf_path):
        return jsonify({'error': 'PDF file not found'}), 404
    
    try:
        # Generate filename based on URL
        from urllib.parse import urlparse
        domain = urlparse(job.url).netloc
        timestamp = job.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"website_pdf_{domain}_{timestamp}.pdf"
        
        return send_file(
            job.pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return jsonify({'error': 'Failed to download PDF'}), 500

@converter_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all conversion jobs"""
    jobs_list = []
    for job_id, job in conversion_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'url': job.url,
            'max_depth': job.max_depth,
            'status': job.status,
            'progress': job.progress,
            'message': job.message,
            'created_at': job.created_at.isoformat(),
            'has_error': job.error is not None
        })
    
    # Sort by creation time (newest first)
    jobs_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({'jobs': jobs_list})

def run_conversion(job):
    """Run the complete conversion process"""
    try:
        # Step 1: Web Crawling
        job.update_status('crawling', 10, 'Starting web crawling...')
        
        crawler = WebCrawler(job.temp_dir)
        crawl_result = crawler.crawl_website(job.url, job.max_depth)
        
        if 'error' in crawl_result:
            job.update_status('failed', error=f"Crawling failed: {crawl_result['error']}")
            return
        
        pages_crawled = crawl_result.get('pages_crawled', 0)
        images_downloaded = crawl_result.get('images_downloaded', 0)
        
        job.update_status('crawling', 40, 
                         f'Crawled {pages_crawled} pages, downloaded {images_downloaded} images')
        
        # Step 2: OCR Processing (if images were found)
        ocr_dir = None
        if images_downloaded > 0:
            job.update_status('ocr', 50, 'Processing images with OCR...')
            
            try:
                from src.ocr_processor import OCRProcessor
                ocr_processor = OCRProcessor(languages=['en'], gpu=False)
                images_dir = os.path.join(job.temp_dir, 'images')
                ocr_dir = os.path.join(job.temp_dir, 'ocr_results')
                
                ocr_summary = ocr_processor.process_directory(images_dir, ocr_dir)
                
                processed = ocr_summary.get('processed_successfully', 0)
                job.update_status('ocr', 70, 
                                 f'OCR completed: {processed}/{images_downloaded} images processed')
                
            except ImportError:
                logger.warning("OCR processor not available, skipping OCR processing")
                job.update_status('ocr', 70, 'OCR not available, skipping image text extraction')
            except Exception as e:
                logger.warning(f"OCR processing failed: {e}")
                job.update_status('ocr', 70, 'OCR processing failed, continuing without OCR')
        else:
            job.update_status('ocr', 70, 'No images found, skipping OCR')
        
        # Step 3: PDF Generation
        job.update_status('generating', 80, 'Generating PDF document...')
        
        pdf_generator = PDFGenerator(job.temp_dir)
        pdf_path = pdf_generator.generate_pdf(job.temp_dir, ocr_dir)
        
        job.pdf_path = pdf_path
        job.update_status('completed', 100, 'Conversion completed successfully!')
        
    except Exception as e:
        logger.error(f"Conversion failed for job {job.job_id}: {e}")
        job.update_status('failed', error=str(e))

# Cleanup old jobs periodically (simple implementation)
def cleanup_old_jobs():
    """Remove old completed jobs to free memory"""
    import time
    current_time = datetime.now()
    
    jobs_to_remove = []
    for job_id, job in conversion_jobs.items():
        # Remove jobs older than 1 hour
        if (current_time - job.created_at).total_seconds() > 3600:
            jobs_to_remove.append(job_id)
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(job.temp_dir, ignore_errors=True)
            except:
                pass
    
    for job_id in jobs_to_remove:
        del conversion_jobs[job_id]
    
    logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

# Start cleanup thread
cleanup_thread = threading.Thread(target=lambda: [
    time.sleep(1800) or cleanup_old_jobs() for _ in iter(int, 1)  # Run every 30 minutes
])
cleanup_thread.daemon = True
cleanup_thread.start()

