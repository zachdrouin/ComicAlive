"""
Project coordinator module to orchestrate the motion comic generation process
"""
import os
import logging
import json
import tempfile
import random
from pathlib import Path

from src.core.file_extractor import ComicFileExtractor
from src.core.image_processor import ImageProcessor
from src.core.audio_generator import AudioGenerator
from src.core.animator import Animator
from src.core.video_renderer import VideoRenderer

logger = logging.getLogger('motion_comic.coordinator')

class ProjectCoordinator:
    """
    Coordinates the motion comic generation process by orchestrating
    the various components
    """
    
    def __init__(self, temp_dir=None):
        """
        Initialize the project coordinator
        
        Args:
            temp_dir: Optional custom temporary directory
        """
        # Use system temp dir if not specified
        if temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="motion_comic_")
        else:
            self.temp_dir = Path(temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)
            
        logger.info(f"Using temporary directory: {self.temp_dir}")
        
        # Initialize components
        self.extractor = ComicFileExtractor()
        self.image_processor = ImageProcessor()
        self.audio_generator = AudioGenerator()
        self.animator = Animator()
        self.video_renderer = VideoRenderer()
        
        # Project data
        self.comic_data = {
            'pages': [],
            'panels': [],
            'animations': {},
            'audio': {}
        }
        
    def extract_comic(self, comic_file_path):
        """
        Extract comic book archive to the temporary directory
        
        Args:
            comic_file_path: Path to the comic book archive
            
        Returns:
            List of extracted image paths
        """
        comic_file_path = Path(comic_file_path)
        logger.info(f"Extracting comic: {comic_file_path}")
        
        # Create extraction directory
        extract_dir = os.path.join(self.temp_dir, "extracted")
        
        # Extract the comic
        extract_dir, image_files = self.extractor.extract(comic_file_path, extract_dir)
        
        # Store page data
        self.comic_data['pages'] = [{
            'id': f"page_{i}",
            'path': path,
            'index': i
        } for i, path in enumerate(image_files)]
        
        logger.info(f"Extracted {len(image_files)} pages")
        return image_files
        
    def process_pages(self, settings=None):
        """
        Process comic pages to detect panels and text
        
        Args:
            settings: Optional settings dictionary
            
        Returns:
            Dictionary containing processed panel data
        """
        logger.info("Processing comic pages")
        
        if not self.comic_data['pages']:
            raise ValueError("No comic pages found. Extract a comic first.")
        
        panels_data = []
        
        # Process each page
        for page in self.comic_data['pages']:
            # Detect panels, text and speech bubbles
            page_data = self.image_processor.process_image(page['path'])
            
            # Add page ID to panels
            for panel in page_data['panels']:
                panel['page_id'] = page['id']
                panel['page_index'] = page['index']
                panels_data.append(panel)
        
        # Store panel data
        self.comic_data['panels'] = panels_data
        
        logger.info(f"Processed {len(panels_data)} panels")
        return panels_data
        
    def create_animations(self, settings=None):
        """
        Create animations for each panel
        
        Args:
            settings: Optional settings dictionary
            
        Returns:
            Dictionary mapping panel IDs to animation frame paths
        """
        logger.info("Creating animations for panels")
        
        if not self.comic_data['panels']:
            raise ValueError("No panels found. Process comic pages first.")
        
        # Apply default settings if not provided
        if settings is None:
            settings = {}
            
        animation_style = settings.get('animation_style', 'pan_and_scan')
        panel_duration = settings.get('panel_duration', 2.5)
        transition_duration = settings.get('transition_duration', 0.5)
        speed_factor = settings.get('animation_speed', 1.0)
        
        # Adjust durations based on speed factor
        panel_duration = panel_duration / speed_factor
        transition_duration = transition_duration / speed_factor
        
        # Create animations for each panel
        animations_data = {}
        
        # Create animation directory
        animation_dir = os.path.join(self.temp_dir, "animations")
        os.makedirs(animation_dir, exist_ok=True)
        
        # Process each panel
        for i, panel in enumerate(self.comic_data['panels']):
            panel_id = panel['id']
            panel_dir = os.path.join(animation_dir, panel_id)
            os.makedirs(panel_dir, exist_ok=True)
            
            # Get original panel image path (from the original page)
            page_path = self.comic_data['pages'][panel['page_index']]['path']
            
            # Extract panel region from the page
            x, y, w, h = panel['region']
            
            # Create animation frames
            if animation_style == 'ken_burns_effect':
                # Use Ken Burns effect
                frames = self.animator.create_ken_burns_effect(
                    page_path,
                    duration=panel_duration,
                    output_dir=panel_dir
                )
            elif animation_style == 'mixed':
                # Use random animation style
                if random.choice([True, False]):
                    frames = self.animator.create_pan_and_scan(
                        page_path,
                        region=(x, y, w, h),
                        duration=panel_duration,
                        output_dir=panel_dir
                    )
                else:
                    frames = self.animator.create_ken_burns_effect(
                        page_path,
                        duration=panel_duration,
                        output_dir=panel_dir
                    )
            else:
                # Default: pan and scan
                frames = self.animator.create_pan_and_scan(
                    page_path,
                    region=(x, y, w, h),
                    duration=panel_duration,
                    output_dir=panel_dir
                )
                
            # Create transitions between panels (except for the first panel)
            if i > 0:
                prev_panel = self.comic_data['panels'][i-1]
                prev_panel_id = prev_panel['id']
                prev_page_path = self.comic_data['pages'][prev_panel['page_index']]['path']
                
                # Create transition directory
                transition_dir = os.path.join(animation_dir, f"transition_{i}")
                os.makedirs(transition_dir, exist_ok=True)
                
                # Create transition frames
                transition_frames = self.animator.create_panel_transition(
                    prev_page_path,
                    page_path,
                    transition_type='fade',
                    duration=transition_duration,
                    output_dir=transition_dir
                )
                
                # Add transition to animations data
                animations_data[f"transition_{i}"] = {
                    'frames': transition_frames,
                    'from_panel': prev_panel_id,
                    'to_panel': panel_id,
                    'type': 'transition'
                }
            
            # Add panel animation to animations data
            animations_data[panel_id] = {
                'frames': frames,
                'panel_index': i,
                'type': 'panel'
            }
        
        # Store animations data
        self.comic_data['animations'] = animations_data
        
        logger.info(f"Created animations for {len(self.comic_data['panels'])} panels")
        return animations_data
        
    def generate_audio(self, settings=None):
        """
        Generate audio for panels based on text content
        
        Args:
            settings: Optional settings dictionary
            
        Returns:
            Dictionary mapping panel IDs to audio file paths
        """
        logger.info("Generating audio for panels")
        
        if not self.comic_data['panels']:
            raise ValueError("No panels found. Process comic pages first.")
            
        # Apply default settings if not provided
        if settings is None:
            settings = {}
            
        voice_name = settings.get('voice_name', 'en-US-Neural2-F')
        voice_pitch = settings.get('voice_pitch', 0)
        voice_speed = settings.get('voice_speed', 1.0)
        enable_sound_effects = settings.get('enable_sound_effects', True)
        
        # Create audio directory
        audio_dir = os.path.join(self.temp_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate audio for each panel
        audio_data = {}
        
        for panel in self.comic_data['panels']:
            panel_id = panel['id']
            
            # Create panel audio directory
            panel_audio_dir = os.path.join(audio_dir, panel_id)
            os.makedirs(panel_audio_dir, exist_ok=True)
            
            # Get text from panel and bubbles
            text_content = panel.get('text', '')
            
            # Also get text from speech bubbles
            for bubble in panel.get('bubbles', []):
                bubble_text = bubble.get('text', '')
                if bubble_text and not bubble_text.isspace():
                    text_content += " " + bubble_text
            
            # Skip if no text content
            if not text_content or text_content.isspace():
                continue
                
            # Use mixed voices for different characters if needed
            if voice_name == 'mixed' and len(panel.get('bubbles', [])) > 1:
                # Create audio for each bubble with a different voice
                bubble_audio_paths = []
                
                voices = ['en-US-Neural2-D', 'en-US-Neural2-F', 'en-US-Neural2-A']
                
                for i, bubble in enumerate(panel.get('bubbles', [])):
                    bubble_text = bubble.get('text', '')
                    if not bubble_text or bubble_text.isspace():
                        continue
                        
                    # Select a voice for this bubble
                    bubble_voice = voices[i % len(voices)]
                    
                    # Generate speech
                    bubble_audio_path = os.path.join(panel_audio_dir, f"bubble_{i}.mp3")
                    audio_path = self.audio_generator.generate_speech(
                        bubble_text,
                        output_path=bubble_audio_path,
                        voice_name=bubble_voice,
                        pitch=voice_pitch,
                        speaking_rate=voice_speed
                    )
                    
                    if audio_path:
                        bubble_audio_paths.append(audio_path)
                
                # Combine all bubble audio
                if bubble_audio_paths:
                    panel_audio_path = os.path.join(panel_audio_dir, "panel_speech.mp3")
                    combined_audio_path = self.audio_generator.combine_audio_tracks(
                        bubble_audio_paths,
                        output_path=panel_audio_path
                    )
                    
                    if combined_audio_path:
                        audio_data[panel_id] = combined_audio_path
            else:
                # Generate single audio for the whole panel
                panel_audio_path = os.path.join(panel_audio_dir, "panel_speech.mp3")
                audio_path = self.audio_generator.generate_speech(
                    text_content,
                    output_path=panel_audio_path,
                    voice_name=voice_name if voice_name != 'mixed' else 'en-US-Neural2-F',
                    pitch=voice_pitch,
                    speaking_rate=voice_speed
                )
                
                if audio_path:
                    audio_data[panel_id] = audio_path
            
            # Add sound effects if enabled
            if enable_sound_effects:
                # Determine which sound effect to use based on the panel content
                # This is a simplistic approach; a more sophisticated system would
                # analyze the image content to determine appropriate sound effects
                
                # Example: add impact sound to action panels (heuristic based on text)
                action_keywords = ['pow', 'bam', 'boom', 'crash', 'bang', 'wham',
                                   'smash', 'crack', 'slam', 'thud', 'whack']
                
                for keyword in action_keywords:
                    if keyword.lower() in text_content.lower():
                        sfx_path = os.path.join(panel_audio_dir, "impact.wav")
                        self.audio_generator.generate_sound_effect('impact', sfx_path)
                        
                        # Combine with speech audio if it exists
                        if panel_id in audio_data:
                            combined_path = os.path.join(panel_audio_dir, "combined.mp3")
                            combined_audio = self.audio_generator.combine_audio_tracks(
                                [audio_data[panel_id], sfx_path],
                                output_path=combined_path
                            )
                            
                            if combined_audio:
                                audio_data[panel_id] = combined_audio
                        else:
                            audio_data[panel_id] = sfx_path
                            
                        break
        
        # Store audio data
        self.comic_data['audio'] = audio_data
        
        logger.info(f"Generated audio for {len(audio_data)} panels")
        return audio_data
        
    def render_video(self, output_path, settings=None):
        """
        Render the final motion comic video
        
        Args:
            output_path: Path to save the output video
            settings: Optional settings dictionary
            
        Returns:
            Path to the rendered video
        """
        logger.info(f"Rendering motion comic video to {output_path}")
        
        # Apply default settings if not provided
        if settings is None:
            settings = {}
            
        fps = settings.get('fps', 24)
        width = settings.get('width', 1920)
        height = settings.get('height', 1080)
        bitrate = settings.get('bitrate', '8000k')
        
        # Configure video renderer
        self.video_renderer = VideoRenderer(
            fps=fps,
            output_width=width,
            output_height=height,
            bitrate=bitrate
        )
        
        # Create video temp directory
        video_dir = os.path.join(self.temp_dir, "video")
        os.makedirs(video_dir, exist_ok=True)
        
        # Gather panel video data
        panel_videos = []
        
        # Process each panel and transition in sequence
        for i, panel in enumerate(self.comic_data['panels']):
            panel_id = panel['id']
            
            # Include transition before panel (except for first panel)
            if i > 0:
                transition_id = f"transition_{i}"
                if transition_id in self.comic_data['animations']:
                    transition_data = self.comic_data['animations'][transition_id]
                    
                    # Create video for transition
                    transition_video_path = os.path.join(video_dir, f"{transition_id}.mp4")
                    self.video_renderer.create_video_from_frames(
                        transition_data['frames'],
                        transition_video_path
                    )
                    
                    panel_videos.append(transition_video_path)
            
            # Skip if panel has no animation
            if panel_id not in self.comic_data['animations']:
                continue
                
            panel_animation = self.comic_data['animations'][panel_id]
            
            # Create video for panel
            panel_video_path = os.path.join(video_dir, f"{panel_id}.mp4")
            self.video_renderer.create_video_from_frames(
                panel_animation['frames'],
                panel_video_path
            )
            
            # Add audio if available
            if panel_id in self.comic_data['audio']:
                audio_path = self.comic_data['audio'][panel_id]
                panel_video_with_audio_path = os.path.join(video_dir, f"{panel_id}_with_audio.mp4")
                
                self.video_renderer.add_audio_to_video(
                    panel_video_path,
                    audio_path,
                    panel_video_with_audio_path
                )
                
                panel_videos.append(panel_video_with_audio_path)
            else:
                panel_videos.append(panel_video_path)
        
        # Combine all panel videos
        if not panel_videos:
            raise ValueError("No panel videos generated. Check animation and panel detection.")
            
        self.video_renderer.combine_videos(panel_videos, output_path)
        
        logger.info(f"Motion comic video rendered: {output_path}")
        return output_path
        
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
            
    def save_project(self, output_path):
        """
        Save the project data to a JSON file
        
        Args:
            output_path: Path to save the project data
            
        Returns:
            Path to the saved project file
        """
        # Create a serializable copy of the data
        # (excluding non-serializable objects and large data)
        serializable_data = {
            'pages': self.comic_data['pages'],
            'panels': self.comic_data['panels'],
            'animations': {
                k: {
                    'panel_index': v.get('panel_index'),
                    'type': v.get('type'),
                    'frame_count': len(v.get('frames', []))
                } for k, v in self.comic_data['animations'].items()
            },
            'audio': {k: str(v) for k, v in self.comic_data['audio'].items()}
        }
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
            
        logger.info(f"Saved project data: {output_path}")
        return output_path
        
    def load_project(self, input_path):
        """
        Load project data from a JSON file
        
        Args:
            input_path: Path to the project file
            
        Returns:
            Loaded project data
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
            
        # Update project data
        self.comic_data.update(data)
        
        logger.info(f"Loaded project data: {input_path}")
        return self.comic_data
