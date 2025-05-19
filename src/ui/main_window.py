"""
Main window UI for the Motion Comic Generator application
"""
import os
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QProgressBar, 
                            QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
                            QCheckBox, QTabWidget, QTextEdit, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage

from src.core.project_coordinator import ProjectCoordinator

logger = logging.getLogger('motion_comic.ui')

class WorkerThread(QThread):
    """Worker thread for running processing tasks in the background"""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, coordinator, input_file, output_file, settings):
        super().__init__()
        self.coordinator = coordinator
        self.input_file = input_file
        self.output_file = output_file
        self.settings = settings
        
    def run(self):
        """Run the processing task"""
        try:
            # Process the comic file
            self.progress_signal.emit(10, "Extracting comic book archive...")
            self.coordinator.extract_comic(self.input_file)
            
            self.progress_signal.emit(20, "Detecting panels and text...")
            self.coordinator.process_pages(self.settings)
            
            self.progress_signal.emit(40, "Generating animations...")
            self.coordinator.create_animations(self.settings)
            
            self.progress_signal.emit(60, "Generating audio...")
            self.coordinator.generate_audio(self.settings)
            
            self.progress_signal.emit(80, "Rendering final video...")
            self.coordinator.render_video(self.output_file, self.settings)
            
            self.progress_signal.emit(100, "Done!")
            self.finished_signal.emit(True, f"Motion comic created successfully: {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error in worker thread: {e}", exc_info=True)
            self.finished_signal.emit(False, f"Error: {str(e)}")


class MainWindow(QMainWindow):
    """Main window for the Motion Comic Generator application"""
    
    def __init__(self):
        super().__init__()
        self.coordinator = ProjectCoordinator()
        self.input_file = None
        self.output_file = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Motion Comic Generator")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        main_tab = QWidget()
        settings_tab = QWidget()
        help_tab = QWidget()
        
        tabs.addTab(main_tab, "Generate")
        tabs.addTab(settings_tab, "Settings")
        tabs.addTab(help_tab, "Help")
        
        # Setup main tab
        main_layout_tab = QVBoxLayout(main_tab)
        
        # Input file section
        input_group = QGroupBox("Input Comic File")
        input_layout = QHBoxLayout()
        self.input_label = QLabel("No file selected")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_input_file)
        input_layout.addWidget(self.input_label, 1)
        input_layout.addWidget(self.browse_button)
        input_group.setLayout(input_layout)
        main_layout_tab.addWidget(input_group)
        
        # Output file section
        output_group = QGroupBox("Output Video File")
        output_layout = QHBoxLayout()
        self.output_label = QLabel("No output file selected")
        self.output_button = QPushButton("Select Output...")
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label, 1)
        output_layout.addWidget(self.output_button)
        output_group.setLayout(output_layout)
        main_layout_tab.addWidget(output_group)
        
        # Animation options section
        animation_group = QGroupBox("Animation Options")
        animation_layout = QVBoxLayout()
        
        # Animation type
        animation_type_layout = QHBoxLayout()
        animation_type_layout.addWidget(QLabel("Animation Style:"))
        self.animation_combo = QComboBox()
        self.animation_combo.addItems(["Pan and Scan", "Ken Burns Effect", "Mixed"])
        animation_type_layout.addWidget(self.animation_combo)
        animation_layout.addLayout(animation_type_layout)
        
        # Animation speed
        animation_speed_layout = QHBoxLayout()
        animation_speed_layout.addWidget(QLabel("Animation Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)
        self.speed_label = QLabel("Medium")
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        animation_speed_layout.addWidget(self.speed_slider)
        animation_speed_layout.addWidget(self.speed_label)
        animation_layout.addLayout(animation_speed_layout)
        
        animation_group.setLayout(animation_layout)
        main_layout_tab.addWidget(animation_group)
        
        # Audio options section
        audio_group = QGroupBox("Audio Options")
        audio_layout = QVBoxLayout()
        
        # Voice type
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice Type:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Male", "Female", "Mixed"])
        voice_layout.addWidget(self.voice_combo)
        audio_layout.addLayout(voice_layout)
        
        # Enable sound effects
        sound_effects_layout = QHBoxLayout()
        self.sound_effects_check = QCheckBox("Enable Sound Effects")
        self.sound_effects_check.setChecked(True)
        sound_effects_layout.addWidget(self.sound_effects_check)
        audio_layout.addLayout(sound_effects_layout)
        
        audio_group.setLayout(audio_layout)
        main_layout_tab.addWidget(audio_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        progress_group.setLayout(progress_layout)
        main_layout_tab.addWidget(progress_group)
        
        # Generate button
        self.generate_button = QPushButton("Generate Motion Comic")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.generate_motion_comic)
        main_layout_tab.addWidget(self.generate_button)
        
        # Setup settings tab
        settings_layout = QVBoxLayout(settings_tab)
        
        # Video settings
        video_settings_group = QGroupBox("Video Settings")
        video_settings_layout = QVBoxLayout()
        
        # Resolution
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["720p (1280x720)", "1080p (1920x1080)", "4K (3840x2160)"])
        self.resolution_combo.setCurrentIndex(1)  # Default to 1080p
        resolution_layout.addWidget(self.resolution_combo)
        video_settings_layout.addLayout(resolution_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frames Per Second:"))
        self.fps_spinner = QSpinBox()
        self.fps_spinner.setMinimum(15)
        self.fps_spinner.setMaximum(60)
        self.fps_spinner.setValue(24)
        fps_layout.addWidget(self.fps_spinner)
        video_settings_layout.addLayout(fps_layout)
        
        # Video quality
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low", "Medium", "High"])
        self.quality_combo.setCurrentIndex(1)  # Default to Medium
        quality_layout.addWidget(self.quality_combo)
        video_settings_layout.addLayout(quality_layout)
        
        video_settings_group.setLayout(video_settings_layout)
        settings_layout.addWidget(video_settings_group)
        
        # Advanced animation settings
        advanced_anim_group = QGroupBox("Advanced Animation Settings")
        advanced_anim_layout = QVBoxLayout()
        
        # Transition duration
        transition_layout = QHBoxLayout()
        transition_layout.addWidget(QLabel("Transition Duration (seconds):"))
        self.transition_spinner = QDoubleSpinBox()
        self.transition_spinner.setMinimum(0.1)
        self.transition_spinner.setMaximum(3.0)
        self.transition_spinner.setValue(0.5)
        self.transition_spinner.setSingleStep(0.1)
        transition_layout.addWidget(self.transition_spinner)
        advanced_anim_layout.addLayout(transition_layout)
        
        # Panel duration
        panel_duration_layout = QHBoxLayout()
        panel_duration_layout.addWidget(QLabel("Panel Duration (seconds):"))
        self.panel_duration_spinner = QDoubleSpinBox()
        self.panel_duration_spinner.setMinimum(1.0)
        self.panel_duration_spinner.setMaximum(10.0)
        self.panel_duration_spinner.setValue(2.5)
        self.panel_duration_spinner.setSingleStep(0.5)
        panel_duration_layout.addWidget(self.panel_duration_spinner)
        advanced_anim_layout.addLayout(panel_duration_layout)
        
        advanced_anim_group.setLayout(advanced_anim_layout)
        settings_layout.addWidget(advanced_anim_group)
        
        # Advanced audio settings
        advanced_audio_group = QGroupBox("Advanced Audio Settings")
        advanced_audio_layout = QVBoxLayout()
        
        # Voice pitch
        voice_pitch_layout = QHBoxLayout()
        voice_pitch_layout.addWidget(QLabel("Voice Pitch:"))
        self.voice_pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.voice_pitch_slider.setMinimum(-10)
        self.voice_pitch_slider.setMaximum(10)
        self.voice_pitch_slider.setValue(0)
        self.voice_pitch_label = QLabel("0")
        self.voice_pitch_slider.valueChanged.connect(lambda v: self.voice_pitch_label.setText(str(v)))
        voice_pitch_layout.addWidget(self.voice_pitch_slider)
        voice_pitch_layout.addWidget(self.voice_pitch_label)
        advanced_audio_layout.addLayout(voice_pitch_layout)
        
        # Voice speed
        voice_speed_layout = QHBoxLayout()
        voice_speed_layout.addWidget(QLabel("Speech Rate:"))
        self.voice_speed_spinner = QDoubleSpinBox()
        self.voice_speed_spinner.setMinimum(0.5)
        self.voice_speed_spinner.setMaximum(2.0)
        self.voice_speed_spinner.setValue(1.0)
        self.voice_speed_spinner.setSingleStep(0.1)
        voice_speed_layout.addWidget(self.voice_speed_spinner)
        advanced_audio_layout.addLayout(voice_speed_layout)
        
        advanced_audio_group.setLayout(advanced_audio_layout)
        settings_layout.addWidget(advanced_audio_group)
        
        # Add spacer to settings layout
        settings_layout.addStretch()
        
        # Setup help tab
        help_layout = QVBoxLayout(help_tab)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Motion Comic Generator Help</h2>
        <p>This application converts comic book archives (.CBR, .CBZ) into animated motion comics with audio.</p>
        
        <h3>Getting Started</h3>
        <ol>
            <li>Click <b>Browse</b> to select a comic book archive file (.CBR or .CBZ)</li>
            <li>Select an output location for your motion comic video</li>
            <li>Adjust animation and audio settings to your preference</li>
            <li>Click <b>Generate Motion Comic</b> to start the conversion process</li>
        </ol>
        
        <h3>Animation Styles</h3>
        <ul>
            <li><b>Pan and Scan</b>: Creates dynamic camera movements across panels</li>
            <li><b>Ken Burns Effect</b>: Creates subtle zoom and pan effects</li>
            <li><b>Mixed</b>: Combines both styles for variety</li>
        </ul>
        
        <h3>Tips</h3>
        <ul>
            <li>Higher quality settings will result in larger file sizes and longer processing times</li>
            <li>You may need to install additional dependencies for audio generation</li>
            <li>For best results, use comics with clear panel layouts and readable text</li>
        </ul>
        """)
        help_layout.addWidget(help_text)
        
        # Add tabs to main layout
        main_layout.addWidget(tabs)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
    def update_speed_label(self, value):
        """Update the animation speed label based on slider value"""
        labels = {
            1: "Very Slow",
            2: "Slow",
            3: "Moderately Slow",
            4: "Below Medium",
            5: "Medium",
            6: "Above Medium",
            7: "Moderately Fast",
            8: "Fast",
            9: "Very Fast",
            10: "Extremely Fast"
        }
        self.speed_label.setText(labels.get(value, "Medium"))
    
    def browse_input_file(self):
        """Open file dialog to select input comic file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Comic Book Archive", "", 
            "Comic Archives (*.cbr *.cbz);;All Files (*)"
        )
        
        if file_path:
            self.input_file = file_path
            self.input_label.setText(os.path.basename(file_path))
            self.update_generate_button()
    
    def select_output_file(self):
        """Open file dialog to select output video file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Select Output Video File", "", 
            "MP4 Video (*.mp4);;All Files (*)"
        )
        
        if file_path:
            # Ensure it has .mp4 extension
            if not file_path.lower().endswith('.mp4'):
                file_path += '.mp4'
                
            self.output_file = file_path
            self.output_label.setText(os.path.basename(file_path))
            self.update_generate_button()
    
    def update_generate_button(self):
        """Enable or disable generate button based on input/output selection"""
        self.generate_button.setEnabled(
            self.input_file is not None and self.output_file is not None
        )
    
    def get_settings(self):
        """Get all settings from the UI controls"""
        # Get resolution dimensions
        resolution_text = self.resolution_combo.currentText()
        if "720p" in resolution_text:
            width, height = 1280, 720
        elif "4K" in resolution_text:
            width, height = 3840, 2160
        else:  # Default to 1080p
            width, height = 1920, 1080
            
        # Get quality settings
        quality = self.quality_combo.currentText().lower()
        if quality == "low":
            bitrate = "2000k"
        elif quality == "high":
            bitrate = "12000k"
        else:  # Medium
            bitrate = "8000k"
        
        # Animation speed factor (1.0 = normal)
        speed_factor = self.speed_slider.value() / 5.0
        
        # Voice settings
        if self.voice_combo.currentText() == "Male":
            voice_name = "en-US-Neural2-D"
        elif self.voice_combo.currentText() == "Female":
            voice_name = "en-US-Neural2-F"
        else:  # Mixed
            voice_name = "mixed"
        
        return {
            # Animation settings
            "animation_style": self.animation_combo.currentText().lower().replace(" ", "_"),
            "animation_speed": speed_factor,
            "transition_duration": self.transition_spinner.value(),
            "panel_duration": self.panel_duration_spinner.value(),
            
            # Audio settings
            "voice_name": voice_name,
            "voice_pitch": self.voice_pitch_slider.value(),
            "voice_speed": self.voice_speed_spinner.value(),
            "enable_sound_effects": self.sound_effects_check.isChecked(),
            
            # Video settings
            "fps": self.fps_spinner.value(),
            "width": width,
            "height": height,
            "bitrate": bitrate
        }
    
    def generate_motion_comic(self):
        """Start the motion comic generation process"""
        if not self.input_file or not self.output_file:
            return
            
        # Disable UI during processing
        self.generate_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.output_button.setEnabled(False)
        
        # Get all settings
        settings = self.get_settings()
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting...")
        
        # Create worker thread
        self.worker = WorkerThread(self.coordinator, self.input_file, self.output_file, settings)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar and message"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def process_finished(self, success, message):
        """Handle process completion"""
        # Re-enable UI
        self.generate_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.output_button.setEnabled(True)
        
        # Show message
        self.progress_label.setText(message)
        
        if success:
            self.progress_bar.setValue(100)
            # TODO: Show dialog with option to open the generated video
        else:
            self.progress_bar.setValue(0)
