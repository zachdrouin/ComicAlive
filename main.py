#!/usr/bin/env python3
"""
Motion Comic Generator - Main Application Entry Point
"""
import sys
import os
from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from src.core.logger import setup_logging

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    # Run the application
    main()
