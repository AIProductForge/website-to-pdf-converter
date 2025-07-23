#!/usr/bin/env python3
"""
OCR Processor Module for Website to PDF Converter
Uses EasyOCR to extract text from images downloaded by the web crawler
"""

import easyocr
import os
import json
import logging
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime

class OCRProcessor:
    """
    OCR processor that extracts text from images using EasyOCR
    """
    
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize OCR processor
        
        Args:
            languages (list): List of language codes for OCR recognition
            gpu (bool): Whether to use GPU acceleration (requires CUDA)
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize EasyOCR reader
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialize the EasyOCR reader"""
        try:
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            self.logger.info(f"EasyOCR reader initialized with languages: {self.languages}")
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR reader: {e}")
            raise
    
    def process_image(self, image_path: str, preprocess: bool = True) -> Dict:
        """
        Process a single image and extract text
        
        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image for better OCR
        
        Returns:
            dict: OCR results with text, confidence, and bounding boxes
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Preprocess image if requested
            if preprocess:
                processed_image = self._preprocess_image(image_path)
            else:
                processed_image = image_path
            
            # Perform OCR
            results = self.reader.readtext(processed_image)
            
            # Process results
            ocr_data = self._process_ocr_results(results, image_path)
            
            self.logger.info(f"OCR completed for {image_path}: {len(ocr_data['text_blocks'])} text blocks found")
            
            return ocr_data
            
        except Exception as e:
            self.logger.error(f"OCR processing failed for {image_path}: {e}")
            return {
                'image_path': image_path,
                'success': False,
                'error': str(e),
                'text_blocks': [],
                'full_text': '',
                'confidence_avg': 0.0,
                'processing_time': datetime.now().isoformat()
            }
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image_path (str): Path to the image file
        
        Returns:
            np.ndarray: Preprocessed image as numpy array
        """
        try:
            # Read image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding to handle varying lighting
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed for {image_path}: {e}")
            # Return original image if preprocessing fails
            return cv2.imread(image_path)
    
    def _process_ocr_results(self, results: List, image_path: str) -> Dict:
        """
        Process raw OCR results into structured format
        
        Args:
            results (list): Raw results from EasyOCR
            image_path (str): Path to the processed image
        
        Returns:
            dict: Structured OCR results
        """
        text_blocks = []
        full_text_parts = []
        confidences = []
        
        for detection in results:
            bbox, text, confidence = detection
            
            # Clean up text
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                continue
            
            # Extract bounding box coordinates
            bbox_coords = {
                'top_left': [float(bbox[0][0]), float(bbox[0][1])],
                'top_right': [float(bbox[1][0]), float(bbox[1][1])],
                'bottom_right': [float(bbox[2][0]), float(bbox[2][1])],
                'bottom_left': [float(bbox[3][0]), float(bbox[3][1])]
            }
            
            text_block = {
                'text': cleaned_text,
                'confidence': float(confidence),
                'bbox': bbox_coords,
                'bbox_area': self._calculate_bbox_area(bbox)
            }
            
            text_blocks.append(text_block)
            full_text_parts.append(cleaned_text)
            confidences.append(confidence)
        
        # Sort text blocks by position (top to bottom, left to right)
        text_blocks = self._sort_text_blocks(text_blocks)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'image_path': image_path,
            'success': True,
            'text_blocks': text_blocks,
            'full_text': ' '.join(full_text_parts),
            'confidence_avg': avg_confidence,
            'processing_time': datetime.now().isoformat()
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text (str): Raw text from OCR
        
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common OCR artifacts
        cleaned = re.sub(r'[^\w\s\.,!?;:()\-\'"/@#$%&*+=\[\]{}|\\`~]', '', cleaned)
        
        return cleaned
    
    def _calculate_bbox_area(self, bbox: List) -> float:
        """
        Calculate the area of a bounding box
        
        Args:
            bbox (list): Bounding box coordinates
        
        Returns:
            float: Area of the bounding box
        """
        try:
            # Calculate width and height
            width = abs(bbox[1][0] - bbox[0][0])
            height = abs(bbox[3][1] - bbox[0][1])
            return width * height
        except:
            return 0.0
    
    def _sort_text_blocks(self, text_blocks: List[Dict]) -> List[Dict]:
        """
        Sort text blocks by reading order (top to bottom, left to right)
        
        Args:
            text_blocks (list): List of text block dictionaries
        
        Returns:
            list: Sorted text blocks
        """
        def sort_key(block):
            bbox = block['bbox']
            # Use top-left corner for sorting
            y = bbox['top_left'][1]  # Y coordinate (top to bottom)
            x = bbox['top_left'][0]  # X coordinate (left to right)
            return (y, x)
        
        return sorted(text_blocks, key=sort_key)
    
    def process_directory(self, image_dir: str, output_dir: str = None) -> Dict:
        """
        Process all images in a directory
        
        Args:
            image_dir (str): Directory containing images
            output_dir (str): Directory to save OCR results (optional)
        
        Returns:
            dict: Summary of processing results
        """
        if not os.path.exists(image_dir):
            raise FileNotFoundError(f"Image directory not found: {image_dir}")
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = [
            f for f in os.listdir(image_dir)
            if os.path.splitext(f.lower())[1] in image_extensions
        ]
        
        if not image_files:
            self.logger.warning(f"No image files found in {image_dir}")
            return {
                'total_images': 0,
                'processed_successfully': 0,
                'failed': 0,
                'results': []
            }
        
        results = []
        successful = 0
        failed = 0
        
        for image_file in image_files:
            image_path = os.path.join(image_dir, image_file)
            
            try:
                ocr_result = self.process_image(image_path)
                results.append(ocr_result)
                
                if ocr_result['success']:
                    successful += 1
                else:
                    failed += 1
                
                # Save individual result if output directory specified
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    result_file = os.path.join(
                        output_dir,
                        f"{os.path.splitext(image_file)[0]}_ocr.json"
                    )
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(ocr_result, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                self.logger.error(f"Failed to process {image_file}: {e}")
                failed += 1
                results.append({
                    'image_path': image_path,
                    'success': False,
                    'error': str(e),
                    'text_blocks': [],
                    'full_text': '',
                    'confidence_avg': 0.0,
                    'processing_time': datetime.now().isoformat()
                })
        
        summary = {
            'total_images': len(image_files),
            'processed_successfully': successful,
            'failed': failed,
            'results': results,
            'processing_time': datetime.now().isoformat()
        }
        
        # Save summary if output directory specified
        if output_dir:
            summary_file = os.path.join(output_dir, 'ocr_summary.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"OCR processing completed: {successful}/{len(image_files)} images processed successfully")
        
        return summary
    
    def get_text_from_results(self, results: List[Dict]) -> str:
        """
        Extract all text from OCR results
        
        Args:
            results (list): List of OCR result dictionaries
        
        Returns:
            str: Combined text from all images
        """
        all_text = []
        
        for result in results:
            if result['success'] and result['full_text'].strip():
                all_text.append(result['full_text'])
        
        return '\n\n'.join(all_text)


def main():
    """Test the OCR processor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <image_path_or_directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Initialize OCR processor
    processor = OCRProcessor(languages=['en'])
    
    if os.path.isfile(input_path):
        # Process single image
        result = processor.process_image(input_path)
        print(f"OCR Result for {input_path}:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Text found: {result['full_text']}")
            print(f"Confidence: {result['confidence_avg']:.2f}")
            print(f"Text blocks: {len(result['text_blocks'])}")
        else:
            print(f"Error: {result['error']}")
    
    elif os.path.isdir(input_path):
        # Process directory
        summary = processor.process_directory(input_path, f"{input_path}_ocr_results")
        print(f"OCR Summary for {input_path}:")
        print(f"Total images: {summary['total_images']}")
        print(f"Successfully processed: {summary['processed_successfully']}")
        print(f"Failed: {summary['failed']}")
        
        # Show text from all images
        all_text = processor.get_text_from_results(summary['results'])
        if all_text:
            print(f"\nCombined text from all images:\n{all_text}")
    
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()

