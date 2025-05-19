"""
Audio generation module for text-to-speech and sound effects
"""
import os
import logging
import tempfile
from pathlib import Path
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from google.cloud import texttospeech

logger = logging.getLogger('motion_comic.audio')

class AudioGenerator:
    """
    Generates audio for motion comics including speech and sound effects
    """
    
    def __init__(self, google_credentials_path=None):
        """
        Initialize the audio generator
        
        Args:
            google_credentials_path: Path to Google Cloud credentials JSON file
        """
        self.google_credentials_path = google_credentials_path
        self.voices_cache = {}
        
        # Set Google credentials environment variable if provided
        if google_credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_credentials_path)
            logger.info(f"Using Google Cloud credentials: {google_credentials_path}")
    
    def generate_speech(self, text, output_path=None, voice_name="en-US-Neural2-F", pitch=0.0, speaking_rate=1.0):
        """
        Generate speech audio from text using Google Cloud TTS
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file (if None, returns path to temp file)
            voice_name: Google Cloud TTS voice name
            pitch: Voice pitch adjustment (-20.0 to 20.0)
            speaking_rate: Voice speed (0.25 to 4.0)
            
        Returns:
            Path to the generated audio file
        """
        if not text or text.isspace():
            logger.warning("Empty text provided for speech generation")
            return None
            
        # Create output path if not provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3", prefix="speech_")
            os.close(fd)
            
        output_path = Path(output_path)
        
        try:
            # Initialize Text-to-Speech client
            client = texttospeech.TextToSpeechClient()
            
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_name.split('-')[0] + '-' + voice_name.split('-')[1],
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                pitch=pitch,
                speaking_rate=speaking_rate
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                
            logger.info(f"Generated speech audio: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            
            # Fallback to simpler speech synthesis method if Google Cloud fails
            return self._generate_speech_fallback(text, output_path)
    
    def _generate_speech_fallback(self, text, output_path):
        """
        Fallback method for speech generation if Google Cloud TTS fails
        """
        logger.warning("Using fallback speech generation method")
        
        try:
            # Generate simple tone pattern as a placeholder
            sample_rate = 22050
            duration = 0.1 * len(text.split())  # Rough approximation
            
            # Generate a simple sine wave tone
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * 440 * t) * 0.3
            
            # Save the audio file
            sf.write(output_path, tone, sample_rate)
            
            logger.info(f"Generated fallback speech audio: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate fallback speech: {e}")
            return None
    
    def generate_sound_effect(self, effect_type, output_path=None, duration=1.0):
        """
        Generate a sound effect
        
        Args:
            effect_type: Type of sound effect ('impact', 'whoosh', etc.)
            output_path: Path to save the audio file (if None, returns path to temp file)
            duration: Duration of the effect in seconds
            
        Returns:
            Path to the generated audio file
        """
        # Create output path if not provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix=f"sfx_{effect_type}_")
            os.close(fd)
            
        output_path = Path(output_path)
        
        try:
            # Generate different sound effects based on type
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            if effect_type == 'impact':
                # Create impact sound (short burst of noise with exponential decay)
                noise = np.random.randn(len(t))
                decay = np.exp(-5 * t)
                signal = noise * decay * 0.5
                
            elif effect_type == 'whoosh':
                # Create whoosh sound (filtered noise with amplitude envelope)
                noise = np.random.randn(len(t))
                envelope = np.sin(np.pi * t / duration)
                signal = noise * envelope * 0.3
                
            elif effect_type == 'page_turn':
                # Create page turning sound (filtered noise with quick attack and decay)
                noise = np.random.randn(len(t))
                envelope = np.exp(-10 * (t - 0.1) ** 2)
                signal = noise * envelope * 0.2
                
            else:
                # Default to white noise with envelope
                noise = np.random.randn(len(t))
                envelope = np.sin(np.pi * t / duration)
                signal = noise * envelope * 0.25
            
            # Save the audio file
            sf.write(output_path, signal, sample_rate)
            
            logger.info(f"Generated sound effect ({effect_type}): {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate sound effect: {e}")
            return None
    
    def combine_audio_tracks(self, audio_paths, output_path=None):
        """
        Combine multiple audio tracks into a single file
        
        Args:
            audio_paths: List of paths to audio files
            output_path: Path to save the combined audio file
            
        Returns:
            Path to the combined audio file
        """
        if not audio_paths:
            logger.warning("No audio paths provided for combining")
            return None
            
        # Create output path if not provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3", prefix="combined_audio_")
            os.close(fd)
            
        output_path = Path(output_path)
        
        try:
            # Load the first audio file
            combined = AudioSegment.from_file(audio_paths[0])
            
            # Overlay additional audio files
            for audio_path in audio_paths[1:]:
                # Load the audio file
                audio = AudioSegment.from_file(audio_path)
                
                # Combine with existing audio (overlay or append)
                combined = combined.overlay(audio)
            
            # Export the combined audio
            combined.export(output_path, format="mp3")
            
            logger.info(f"Combined {len(audio_paths)} audio tracks: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to combine audio tracks: {e}")
            return None
