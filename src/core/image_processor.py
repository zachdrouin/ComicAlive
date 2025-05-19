"""
Image processing module for panel detection and segmentation in comic book pages
"""
import cv2
import numpy as np
import logging
from pathlib import Path
import pytesseract
from PIL import Image

logger = logging.getLogger('motion_comic.image_processor')

class ImageProcessor:
    """
    Processes comic book images to detect panels, text, and characters
    """
    
    def __init__(self, min_panel_size=0.01, max_panel_size=0.9):
        """
        Initialize the image processor
        
        Args:
            min_panel_size: Minimum panel size as a fraction of the image area
            max_panel_size: Maximum panel size as a fraction of the image area
        """
        self.min_panel_size = min_panel_size
        self.max_panel_size = max_panel_size
        
    def process_image(self, image_path):
        """
        Process a comic book page image to detect panels, text and characters
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing panel regions, text regions and character regions
        """
        image_path = Path(image_path)
        logger.info(f"Processing image: {image_path}")
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Get image dimensions
        height, width = image.shape[:2]
        image_area = height * width
        
        # Detect panels
        panels = self.detect_panels(image)
        
        # Filter panels by size
        min_area = self.min_panel_size * image_area
        max_area = self.max_panel_size * image_area
        filtered_panels = []
        
        for panel in panels:
            x, y, w, h = panel
            panel_area = w * h
            if min_area <= panel_area <= max_area:
                filtered_panels.append(panel)
        
        # Process each panel
        panel_data = []
        for i, panel in enumerate(filtered_panels):
            x, y, w, h = panel
            panel_image = image[y:y+h, x:x+w]
            
            # Extract text using OCR
            text = self.extract_text(panel_image)
            
            # Detect speech bubbles
            bubbles = self.detect_speech_bubbles(panel_image)
            
            # Process each bubble
            bubble_data = []
            for j, bubble in enumerate(bubbles):
                bx, by, bw, bh = bubble
                bubble_image = panel_image[by:by+bh, bx:bx+bw]
                bubble_text = self.extract_text(bubble_image)
                
                bubble_data.append({
                    'id': f'bubble_{i}_{j}',
                    'region': (bx, by, bw, bh),
                    'text': bubble_text
                })
            
            panel_data.append({
                'id': f'panel_{i}',
                'region': (x, y, w, h),
                'text': text,
                'bubbles': bubble_data
            })
        
        result = {
            'image_path': str(image_path),
            'dimensions': (width, height),
            'panels': panel_data
        }
        
        logger.info(f"Processed image with {len(filtered_panels)} panels")
        return result
    
    def detect_panels(self, image):
        """
        Detect panels in a comic book page
        
        Args:
            image: OpenCV image object
            
        Returns:
            List of panel regions as (x, y, width, height) tuples
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get bounding rectangles for contours
        panels = [cv2.boundingRect(contour) for contour in contours]
        
        # Sort panels from top to bottom, left to right
        panels.sort(key=lambda x: (x[1], x[0]))
        
        return panels
    
    def detect_speech_bubbles(self, image):
        """
        Detect speech bubbles in a comic panel
        
        Args:
            image: OpenCV image object
            
        Returns:
            List of bubble regions as (x, y, width, height) tuples
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Get bounding rectangles for contours that are likely to be speech bubbles
        bubbles = []
        for contour in contours:
            # Get contour area
            area = cv2.contourArea(contour)
            
            # Filter out small contours
            if area < 100:
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Compute aspect ratio
            aspect_ratio = float(w) / h
            
            # Compute solidity (area / convex hull area)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            
            # Filter based on shape properties (speech bubbles tend to be rounder)
            if 0.5 <= aspect_ratio <= 2.0 and solidity > 0.7:
                bubbles.append((x, y, w, h))
        
        return bubbles
    
    def extract_text(self, image):
        """
        Extract text from an image using OCR
        
        Args:
            image: OpenCV image object
            
        Returns:
            Extracted text as a string
        """
        # Convert from OpenCV format to PIL format
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Use Tesseract OCR to extract text
        text = pytesseract.image_to_string(pil_image, lang='eng')
        
        return text.strip()
    
    def highlight_panels(self, image_path, output_path=None):
        """
        Create a debug visualization showing detected panels
        
        Args:
            image_path: Path to the input image
            output_path: Path to save the visualization (if None, returns the image)
            
        Returns:
            Visualization image if output_path is None, otherwise None
        """
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Get panels
        panels = self.detect_panels(image)
        
        # Create a copy for visualization
        viz_image = image.copy()
        
        # Draw rectangles around panels
        for i, (x, y, w, h) in enumerate(panels):
            cv2.rectangle(viz_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(viz_image, f"Panel {i+1}", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Save or return the image
        if output_path:
            cv2.imwrite(str(output_path), viz_image)
            return None
        else:
            return viz_image
