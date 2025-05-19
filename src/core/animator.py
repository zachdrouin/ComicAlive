"""
Animation module for creating motion effects in comic panels
"""
import cv2
import numpy as np
import logging
from pathlib import Path
import os
import tempfile

logger = logging.getLogger('motion_comic.animator')

class Animator:
    """
    Creates motion effects for comic book panels
    """
    
    def __init__(self, fps=24, transition_duration=0.5):
        """
        Initialize the animator
        
        Args:
            fps: Frames per second for animations
            transition_duration: Default duration for transitions in seconds
        """
        self.fps = fps
        self.transition_duration = transition_duration
        
    def create_pan_and_scan(self, image_path, region=None, duration=2.0, output_dir=None):
        """
        Create a pan and scan animation for a panel
        
        Args:
            image_path: Path to the panel image
            region: Region to focus on (x, y, width, height) or None for full image
            duration: Duration of the animation in seconds
            output_dir: Directory to save the animation frames
            
        Returns:
            List of paths to the animation frames
        """
        image_path = Path(image_path)
        
        # Create output directory if not provided
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="anim_")
        else:
            os.makedirs(output_dir, exist_ok=True)
            
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Calculate total number of frames
        total_frames = int(duration * self.fps)
        
        # If no region specified, use random pan across the image
        if region is None:
            # Define start and end zoom levels (1.0 = full image)
            start_zoom = 1.0
            end_zoom = 1.5
            
            # Define random start and end positions for the pan
            start_x = np.random.randint(0, int(width * 0.1))
            start_y = np.random.randint(0, int(height * 0.1))
            end_x = np.random.randint(int(width * 0.1), int(width * 0.2))
            end_y = np.random.randint(int(height * 0.1), int(height * 0.2))
        else:
            # Use the specified region for a focused zoom
            x, y, w, h = region
            
            # Start with the full image
            start_zoom = 1.0
            start_x = 0
            start_y = 0
            
            # End with a zoom on the region
            end_zoom = min(width / w, height / h) * 0.8
            end_x = max(0, x - (width / end_zoom - w) / 2)
            end_y = max(0, y - (height / end_zoom - h) / 2)
        
        # Generate animation frames
        frame_paths = []
        
        for i in range(total_frames):
            # Calculate interpolation factor (0.0 to 1.0)
            t = i / (total_frames - 1) if total_frames > 1 else 0
            
            # Apply ease-in-out interpolation
            if t < 0.5:
                f = 2 * t * t
            else:
                f = 1 - pow(-2 * t + 2, 2) / 2
            
            # Interpolate zoom and position
            zoom = start_zoom + f * (end_zoom - start_zoom)
            x = start_x + f * (end_x - start_x)
            y = start_y + f * (end_y - start_y)
            
            # Calculate the size of the cropped region
            crop_width = int(width / zoom)
            crop_height = int(height / zoom)
            
            # Ensure crop region is within image bounds
            x = min(max(0, int(x)), width - crop_width)
            y = min(max(0, int(y)), height - crop_height)
            
            # Crop the image
            crop = image[y:y+crop_height, x:x+crop_width]
            
            # Resize back to original size
            frame = cv2.resize(crop, (width, height), interpolation=cv2.INTER_CUBIC)
            
            # Save the frame
            frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
        
        logger.info(f"Created pan and scan animation with {len(frame_paths)} frames")
        return frame_paths
    
    def create_ken_burns_effect(self, image_path, duration=2.0, output_dir=None):
        """
        Create a Ken Burns effect (slow pan and zoom) for an image
        
        Args:
            image_path: Path to the image
            duration: Duration of the animation in seconds
            output_dir: Directory to save the animation frames
            
        Returns:
            List of paths to the animation frames
        """
        image_path = Path(image_path)
        
        # Create output directory if not provided
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="ken_burns_")
        else:
            os.makedirs(output_dir, exist_ok=True)
            
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Calculate total number of frames
        total_frames = int(duration * self.fps)
        
        # Randomly choose zoom in or zoom out
        zoom_in = np.random.choice([True, False])
        
        if zoom_in:
            # Zoom in effect
            start_scale = 1.0
            end_scale = 1.3
        else:
            # Zoom out effect
            start_scale = 1.3
            end_scale = 1.0
        
        # Calculate the maximum possible offset to keep image in frame
        max_x_offset = int(width * (max(start_scale, end_scale) - 1))
        max_y_offset = int(height * (max(start_scale, end_scale) - 1))
        
        # Choose random start and end positions
        start_x = np.random.randint(0, max(1, max_x_offset))
        start_y = np.random.randint(0, max(1, max_y_offset))
        end_x = np.random.randint(0, max(1, max_x_offset))
        end_y = np.random.randint(0, max(1, max_y_offset))
        
        # Generate animation frames
        frame_paths = []
        
        for i in range(total_frames):
            # Calculate interpolation factor (0.0 to 1.0)
            t = i / (total_frames - 1) if total_frames > 1 else 0
            
            # Apply smooth interpolation
            scale = start_scale + t * (end_scale - start_scale)
            x_offset = int(start_x + t * (end_x - start_x))
            y_offset = int(start_y + t * (end_y - start_y))
            
            # Create transformation matrix
            M = cv2.getRotationMatrix2D((width/2, height/2), 0, scale)
            M[0, 2] += -x_offset
            M[1, 2] += -y_offset
            
            # Apply transformation
            frame = cv2.warpAffine(image, M, (width, height), 
                                   borderMode=cv2.BORDER_CONSTANT, 
                                   borderValue=(0, 0, 0))
            
            # Save the frame
            frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
        
        logger.info(f"Created Ken Burns effect with {len(frame_paths)} frames")
        return frame_paths
    
    def create_panel_transition(self, from_image_path, to_image_path, transition_type='fade', 
                               duration=None, output_dir=None):
        """
        Create a transition between two panels
        
        Args:
            from_image_path: Path to the first panel image
            to_image_path: Path to the second panel image
            transition_type: Type of transition ('fade', 'slide', 'zoom')
            duration: Duration of the transition in seconds
            output_dir: Directory to save the transition frames
            
        Returns:
            List of paths to the transition frames
        """
        from_image_path = Path(from_image_path)
        to_image_path = Path(to_image_path)
        
        # Use default duration if not specified
        if duration is None:
            duration = self.transition_duration
            
        # Create output directory if not provided
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="transition_")
        else:
            os.makedirs(output_dir, exist_ok=True)
            
        # Load images
        from_image = cv2.imread(str(from_image_path))
        to_image = cv2.imread(str(to_image_path))
        
        if from_image is None or to_image is None:
            raise ValueError("Failed to load one or both images")
            
        # Resize second image to match first if needed
        if from_image.shape[:2] != to_image.shape[:2]:
            to_image = cv2.resize(to_image, (from_image.shape[1], from_image.shape[0]))
            
        # Calculate total number of frames
        total_frames = int(duration * self.fps)
        
        # Generate transition frames
        frame_paths = []
        
        for i in range(total_frames):
            # Calculate interpolation factor (0.0 to 1.0)
            t = i / (total_frames - 1) if total_frames > 1 else 0
            
            if transition_type == 'fade':
                # Fade transition
                frame = cv2.addWeighted(from_image, 1 - t, to_image, t, 0)
                
            elif transition_type == 'slide':
                # Slide transition (from right to left)
                frame = np.zeros_like(from_image)
                offset = int(from_image.shape[1] * t)
                
                # Copy portions of both images
                if offset > 0:
                    frame[:, :from_image.shape[1]-offset] = from_image[:, offset:]
                if offset < from_image.shape[1]:
                    frame[:, from_image.shape[1]-offset:] = to_image[:, :offset]
                    
            elif transition_type == 'zoom':
                # Zoom transition
                # Scale the second image and overlay on first
                scale = t
                if scale > 0:
                    h, w = from_image.shape[:2]
                    scaled_h, scaled_w = int(h * scale), int(w * scale)
                    
                    if scaled_h > 0 and scaled_w > 0:
                        # Resize the second image
                        resized = cv2.resize(to_image, (scaled_w, scaled_h))
                        
                        # Calculate position to place the resized image
                        y_offset = (h - scaled_h) // 2
                        x_offset = (w - scaled_w) // 2
                        
                        # Start with the first image
                        frame = from_image.copy()
                        
                        # Overlay the resized second image
                        frame[y_offset:y_offset+scaled_h, x_offset:x_offset+scaled_w] = resized
                    else:
                        frame = from_image.copy()
                else:
                    frame = from_image.copy()
                    
            else:
                # Default: cross-dissolve
                frame = cv2.addWeighted(from_image, 1 - t, to_image, t, 0)
            
            # Save the frame
            frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
        
        logger.info(f"Created {transition_type} transition with {len(frame_paths)} frames")
        return frame_paths
