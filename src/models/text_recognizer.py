"""
Text recognizer module for comic book images
Uses OCR (Optical Character Recognition) to extract text from speech bubbles and captions
"""
import cv2
import numpy as np
import pytesseract
import logging
from PIL import Image

logger = logging.getLogger('motion_comic.models.text_recognizer')

class TextRecognizer:
    """
    Recognizes and extracts text from comic book images using OCR
    """
    
    def __init__(self, lang='eng', config='--psm 6'):
        """
        Initialize the text recognizer
        
        Args:
            lang: Language for OCR (default: English)
            config: Tesseract configuration
        """
        self.lang = lang
        self.config = config
        
    def extract_text(self, image, region=None):
        """
        Extract text from an image using OCR
        
        Args:
            image: OpenCV image or path to image file
            region: Optional region to extract text from (x, y, width, height)
            
        Returns:
            Extracted text as a string
        """
        # Load image if it's a file path
        if isinstance(image, str):
            image = cv2.imread(image)
            
        if image is None:
            logger.error("Failed to load image for text extraction")
            return ""
            
        # Extract region if specified
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
            
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Apply preprocessing to improve OCR results
        processed = self._preprocess_for_ocr(gray)
        
        # Convert from OpenCV to PIL format
        pil_image = Image.fromarray(processed)
        
        # Extract text using Tesseract OCR
        try:
            text = pytesseract.image_to_string(pil_image, lang=self.lang, config=self.config)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def _preprocess_for_ocr(self, image):
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: Grayscale image
            
        Returns:
            Preprocessed image
        """
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 7
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def detect_speech_bubbles(self, image):
        """
        Detect speech bubbles in a comic panel
        
        Args:
            image: OpenCV image
            
        Returns:
            List of speech bubble regions (x, y, width, height)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Apply thresholding
        _, binary = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubbles = []
        for contour in contours:
            # Compute area
            area = cv2.contourArea(contour)
            
            # Skip very small contours
            if area < 500:
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio and solidity
            aspect_ratio = float(w) / h if h > 0 else 0
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            
            # Speech bubbles tend to have certain characteristics
            if 0.3 <= aspect_ratio <= 3.0 and solidity > 0.7:
                bubbles.append((x, y, w, h))
        
        return bubbles
    
    def extract_text_from_bubbles(self, image, bubbles):
        """
        Extract text from speech bubbles
        
        Args:
            image: OpenCV image
            bubbles: List of speech bubble regions
            
        Returns:
            Dictionary mapping bubble regions to extracted text
        """
        results = {}
        
        for i, bubble in enumerate(bubbles):
            # Extract text from bubble
            text = self.extract_text(image, bubble)
            
            # Skip if no text was found
            if not text or text.isspace():
                continue
                
            results[i] = {
                'region': bubble,
                'text': text
            }
        
        return results
