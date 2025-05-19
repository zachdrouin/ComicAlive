"""
File extraction module for CBR (Comic Book RAR) archives
"""
import os
import shutil
import tempfile
import logging
import zipfile
import subprocess
from pathlib import Path

logger = logging.getLogger('motion_comic.extractor')

class ComicFileExtractor:
    """
    Extracts comic book archive files (CBR, CBZ) into individual images
    """
    
    def __init__(self, temp_dir=None):
        """
        Initialize extractor with optional custom temp directory
        
        Args:
            temp_dir: Optional custom temp directory path
        """
        self.temp_dir = temp_dir
        self.supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        
    def extract(self, file_path, output_dir=None):
        """
        Extract a comic book archive to the specified output directory
        
        Args:
            file_path: Path to the comic book archive file
            output_dir: Directory to extract files to (if None, uses a temp dir)
            
        Returns:
            Path to the directory containing extracted files
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Create a temporary directory if output_dir is not specified
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="comic_extract_")
        else:
            os.makedirs(output_dir, exist_ok=True)
            
        logger.info(f"Extracting {file_path} to {output_dir}")
        
        # Extract based on file extension
        if file_path.suffix.lower() == '.cbz':
            self._extract_cbz(file_path, output_dir)
        elif file_path.suffix.lower() == '.cbr':
            self._extract_cbr(file_path, output_dir)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
        # Get sorted list of image files
        image_files = self._get_sorted_image_files(output_dir)
        
        logger.info(f"Extracted {len(image_files)} images")
        return output_dir, image_files
    
    def _extract_cbz(self, file_path, output_dir):
        """Extract a CBZ (Comic Book ZIP) file"""
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
    
    def _extract_cbr(self, file_path, output_dir):
        """
        Extract a CBR (Comic Book RAR) file using unrar or 7z 
        Requires either unrar or 7z to be installed on the system
        """
        # Try using unrar command
        try:
            result = subprocess.run(
                ['unrar', 'x', str(file_path), output_dir], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            logger.debug(f"unrar output: {result.stdout.decode()}")
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("unrar command failed, trying 7z")
            
        # Try using 7z command
        try:
            result = subprocess.run(
                ['7z', 'x', str(file_path), f'-o{output_dir}'],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            logger.debug(f"7z output: {result.stdout.decode()}")
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RuntimeError("Failed to extract CBR file. Make sure unrar or 7z is installed.")
    
    def _get_sorted_image_files(self, directory):
        """Get a sorted list of image files in the directory"""
        image_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(self.supported_extensions):
                    image_files.append(os.path.join(root, file))
        
        # Sort files naturally (so page10 comes after page9, not after page1)
        return sorted(image_files, key=self._natural_sort_key)
    
    @staticmethod
    def _natural_sort_key(s):
        """Key function for natural sorting"""
        import re
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', str(s))]

    def cleanup(self, directory):
        """
        Clean up temporary directory
        
        Args:
            directory: Directory to remove
        """
        if os.path.exists(directory) and os.path.isdir(directory):
            shutil.rmtree(directory)
            logger.info(f"Cleaned up temporary directory: {directory}")
