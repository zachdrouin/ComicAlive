"""
Video renderer module for combining animations and audio into a final motion comic
"""
import os
import logging
from pathlib import Path
import tempfile
import subprocess
import json
import cv2
import numpy as np

logger = logging.getLogger('motion_comic.video_renderer')

class VideoRenderer:
    """
    Renders the final motion comic video by combining panel animations with audio
    """
    
    def __init__(self, fps=24, output_width=1920, output_height=1080, bitrate="8000k"):
        """
        Initialize the video renderer
        
        Args:
            fps: Frames per second for the output video
            output_width: Width of the output video
            output_height: Height of the output video
            bitrate: Bitrate for the output video
        """
        self.fps = fps
        self.output_width = output_width
        self.output_height = output_height
        self.bitrate = bitrate
    
    def create_sequence_file(self, sequence_data, output_path):
        """
        Create a sequence file for ffmpeg to use
        
        Args:
            sequence_data: List of dictionaries containing frame paths and durations
            output_path: Path to save the sequence file
            
        Returns:
            Path to the sequence file
        """
        with open(output_path, 'w') as f:
            for item in sequence_data:
                # Format: filename duration
                f.write(f"file '{item['frame']}'\n")
                f.write(f"duration {item['duration']}\n")
                
        logger.info(f"Created sequence file: {output_path}")
        return output_path
    
    def create_video_from_frames(self, frame_paths, output_path, frame_duration=None):
        """
        Create a video from a list of image frames
        
        Args:
            frame_paths: List of paths to image frames
            output_path: Path to save the video
            frame_duration: Duration for each frame in seconds or None to use fps
            
        Returns:
            Path to the generated video
        """
        if not frame_paths:
            raise ValueError("No frames provided for video creation")
            
        output_path = Path(output_path)
        
        # Create a temporary sequence file
        fd, sequence_file = tempfile.mkstemp(suffix=".txt", prefix="sequence_")
        os.close(fd)
        
        # Prepare sequence data
        sequence_data = []
        
        # If frame_duration is specified, use it for all frames
        if frame_duration is not None:
            for frame_path in frame_paths:
                sequence_data.append({
                    'frame': frame_path,
                    'duration': frame_duration
                })
        else:
            # Use 1/fps for each frame duration
            frame_duration = 1.0 / self.fps
            for frame_path in frame_paths:
                sequence_data.append({
                    'frame': frame_path,
                    'duration': frame_duration
                })
        
        # Create the sequence file
        self.create_sequence_file(sequence_data, sequence_file)
        
        # Prepare ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', sequence_file,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease,pad={self.output_width}:{self.output_height}:(ow-iw)/2:(oh-ih)/2',
            str(output_path)
        ]
        
        try:
            # Run ffmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Created video from {len(frame_paths)} frames: {output_path}")
            
            # Clean up the sequence file
            os.remove(sequence_file)
            
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create video: {e.stderr.decode()}")
            raise RuntimeError("Failed to create video from frames")
    
    def add_audio_to_video(self, video_path, audio_path, output_path):
        """
        Add audio to a video file
        
        Args:
            video_path: Path to the video file
            audio_path: Path to the audio file
            output_path: Path to save the combined video
            
        Returns:
            Path to the combined video
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_path = Path(output_path)
        
        # Prepare ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            str(output_path)
        ]
        
        try:
            # Run ffmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Added audio to video: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add audio to video: {e.stderr.decode()}")
            raise RuntimeError("Failed to add audio to video")
    
    def combine_videos(self, video_paths, output_path):
        """
        Combine multiple videos into a single video
        
        Args:
            video_paths: List of paths to video files
            output_path: Path to save the combined video
            
        Returns:
            Path to the combined video
        """
        if not video_paths:
            raise ValueError("No videos provided for combining")
            
        # Create a temporary file for the list of videos
        fd, video_list_file = tempfile.mkstemp(suffix=".txt", prefix="video_list_")
        os.close(fd)
        
        # Write the list of videos to the file
        with open(video_list_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        # Prepare ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', video_list_file,
            '-c', 'copy',
            str(output_path)
        ]
        
        try:
            # Run ffmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Combined {len(video_paths)} videos: {output_path}")
            
            # Clean up the temp file
            os.remove(video_list_file)
            
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to combine videos: {e.stderr.decode()}")
            raise RuntimeError("Failed to combine videos")
    
    def create_motion_comic(self, panel_data, audio_data, output_path, temp_dir=None):
        """
        Create a complete motion comic from panel data and audio data
        
        Args:
            panel_data: List of dictionaries containing panel information and frame paths
            audio_data: Dictionary mapping panel IDs to audio file paths
            output_path: Path to save the final motion comic
            temp_dir: Directory for temporary files
            
        Returns:
            Path to the final motion comic
        """
        if not panel_data:
            raise ValueError("No panel data provided for motion comic creation")
            
        output_path = Path(output_path)
        
        # Create temp directory if not provided
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="motion_comic_")
        else:
            temp_dir = Path(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
        
        # Process each panel to create individual video segments
        panel_videos = []
        
        for i, panel in enumerate(panel_data):
            panel_id = panel.get('id', f'panel_{i}')
            frames = panel.get('frames', [])
            
            if not frames:
                logger.warning(f"No frames found for panel {panel_id}")
                continue
            
            # Create video for this panel
            panel_video_path = os.path.join(temp_dir, f"{panel_id}_video.mp4")
            self.create_video_from_frames(frames, panel_video_path)
            
            # Add audio if available
            if panel_id in audio_data:
                audio_path = audio_data[panel_id]
                panel_video_with_audio_path = os.path.join(temp_dir, f"{panel_id}_with_audio.mp4")
                self.add_audio_to_video(panel_video_path, audio_path, panel_video_with_audio_path)
                panel_videos.append(panel_video_with_audio_path)
            else:
                panel_videos.append(panel_video_path)
        
        # Combine all panel videos
        self.combine_videos(panel_videos, output_path)
        
        logger.info(f"Created motion comic with {len(panel_videos)} panel videos: {output_path}")
        return str(output_path)
    
    def add_subtitles(self, video_path, subtitles_data, output_path=None):
        """
        Add subtitles to a video
        
        Args:
            video_path: Path to the video file
            subtitles_data: List of dictionaries with text and timing information
            output_path: Path to save the video with subtitles
            
        Returns:
            Path to the video with subtitles
        """
        video_path = Path(video_path)
        
        if output_path is None:
            output_path = video_path.with_name(f"{video_path.stem}_with_subs{video_path.suffix}")
        
        # Create SRT file
        fd, srt_path = tempfile.mkstemp(suffix=".srt", prefix="subtitles_")
        os.close(fd)
        
        with open(srt_path, 'w') as f:
            for i, subtitle in enumerate(subtitles_data):
                # Extract subtitle information
                text = subtitle.get('text', '')
                start_time = subtitle.get('start_time', 0)
                end_time = subtitle.get('end_time', start_time + 2)
                
                # Convert times to SRT format (HH:MM:SS,mmm)
                start_str = self._format_time_for_srt(start_time)
                end_str = self._format_time_for_srt(end_time)
                
                # Write subtitle entry
                f.write(f"{i+1}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{text}\n\n")
        
        # Prepare ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vf', f"subtitles={srt_path}",
            '-c:a', 'copy',
            str(output_path)
        ]
        
        try:
            # Run ffmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Added subtitles to video: {output_path}")
            
            # Clean up the SRT file
            os.remove(srt_path)
            
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add subtitles to video: {e.stderr.decode()}")
            raise RuntimeError("Failed to add subtitles to video")
    
    @staticmethod
    def _format_time_for_srt(seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
