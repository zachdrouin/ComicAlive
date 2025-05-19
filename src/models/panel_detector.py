"""
Panel detector model for comic book images
This module contains the implementation of a panel detector using computer vision techniques
"""
import cv2
import numpy as np
import logging
import os
from pathlib import Path

logger = logging.getLogger('motion_comic.models.panel_detector')

class PanelDetector:
    """
    Detects panels in comic book pages using computer vision techniques
    Uses a combination of edge detection, morphological operations,
    and contour analysis to identify panel boundaries
    """
    
    def __init__(self, min_panel_ratio=0.01, max_panel_ratio=0.9):
        """
        Initialize the panel detector
        
        Args:
            min_panel_ratio: Minimum panel size as a ratio of the page area
            max_panel_ratio: Maximum panel size as a ratio of the page area
        """
        self.min_panel_ratio = min_panel_ratio
        self.max_panel_ratio = max_panel_ratio
        
    def detect(self, image):
        """
        Detect panels in a comic book page
        
        Args:
            image: OpenCV image (numpy array)
            
        Returns:
            List of panel regions as (x, y, width, height) tuples
        """
        # Get image dimensions
        height, width = image.shape[:2]
        image_area = height * width
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Threshold the image to get high contrast
        _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
        
        # Apply morphological operations to enhance panel boundaries
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=2)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape
        panels = []
        min_area = self.min_panel_ratio * image_area
        max_area = self.max_panel_ratio * image_area
        
        for contour in contours:
            # Get contour area
            area = cv2.contourArea(contour)
            
            # Skip if too small or too large
            if area < min_area or area > max_area:
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio
            aspect_ratio = float(w) / h if h > 0 else 0
            
            # Skip if aspect ratio is extreme
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                continue
                
            # Skip if too close to the edge (partial panels)
            edge_margin = int(min(width, height) * 0.01)
            if x < edge_margin and y < edge_margin:
                continue
                
            panels.append((x, y, w, h))
        
        # Merge overlapping panels
        merged_panels = self._merge_overlapping_panels(panels)
        
        # Sort panels from top to bottom, left to right
        merged_panels.sort(key=lambda p: (p[1], p[0]))
        
        return merged_panels
    
    def _merge_overlapping_panels(self, panels, overlap_threshold=0.3):
        """
        Merge overlapping panel regions
        
        Args:
            panels: List of panel regions as (x, y, width, height) tuples
            overlap_threshold: Threshold for considering panels as overlapping
            
        Returns:
            List of merged panel regions
        """
        if not panels:
            return []
            
        # Sort panels by area (largest first)
        panels = sorted(panels, key=lambda p: p[2] * p[3], reverse=True)
        
        merged = []
        used = [False] * len(panels)
        
        for i, panel_i in enumerate(panels):
            if used[i]:
                continue
                
            x1, y1, w1, h1 = panel_i
            merged_panel = list(panel_i)
            used[i] = True
            
            # Check against other panels
            for j, panel_j in enumerate(panels):
                if used[j] or i == j:
                    continue
                    
                x2, y2, w2, h2 = panel_j
                
                # Calculate overlap area
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                area_i = w1 * h1
                area_j = w2 * h2
                
                # If panels overlap significantly, merge them
                smaller_area = min(area_i, area_j)
                if overlap_area > overlap_threshold * smaller_area:
                    # Create a bounding box that encompasses both panels
                    x = min(x1, x2)
                    y = min(y1, y2)
                    w = max(x1 + w1, x2 + w2) - x
                    h = max(y1 + h1, y2 + h2) - y
                    
                    merged_panel = [x, y, w, h]
                    x1, y1, w1, h1 = merged_panel
                    used[j] = True
            
            merged.append(tuple(merged_panel))
        
        return merged
    
    def visualize_panels(self, image, panels, output_path=None):
        """
        Create a visualization of detected panels
        
        Args:
            image: Original image
            panels: List of panel regions
            output_path: Path to save the visualization image
            
        Returns:
            Visualization image
        """
        # Make a copy of the image
        vis_image = image.copy()
        
        # Draw rectangles for each panel
        for i, (x, y, w, h) in enumerate(panels):
            cv2.rectangle(vis_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(vis_image, f"Panel {i+1}", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Save if output path is provided
        if output_path:
            cv2.imwrite(output_path, vis_image)
            
        return vis_image
    
    def extract_panel_images(self, image, panels, output_dir=None):
        """
        Extract individual panel images from the full page
        
        Args:
            image: Original image
            panels: List of panel regions
            output_dir: Directory to save extracted panel images
            
        Returns:
            List of panel images or paths to saved images
        """
        # Create output directory if provided
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        panel_images = []
        
        # Extract each panel
        for i, (x, y, w, h) in enumerate(panels):
            # Extract panel image
            panel_image = image[y:y+h, x:x+w]
            
            # Save if output directory is provided
            if output_dir:
                output_path = os.path.join(output_dir, f"panel_{i:03d}.jpg")
                cv2.imwrite(output_path, panel_image)
                panel_images.append(output_path)
            else:
                panel_images.append(panel_image)
        
        return panel_images
