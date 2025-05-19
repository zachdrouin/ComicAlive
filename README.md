# Comic Alive

An AI-powered tool that converts comic book archives (CBR/CBZ) into engaging motion comic videos with animation, speech, and sound.

An AI-powered tool that converts CBR comic book archives into engaging motion comic videos.

## Features

- Automatic CBR file extraction
- Panel detection and segmentation
- Text and character recognition
- AI-driven animations
- AI-generated audio (dialogues and sound effects)
- Video rendering capabilities
- User-friendly GUI interface

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up Google Cloud credentials for TTS (optional)

## Usage

```python
python main.py
```

## Project Structure

- `src/`: Main source code
- `models/`: Pre-trained models
- `data/`: Sample data and test files
- `output/`: Generated motion comics

## Dependencies

- Python 3.8+
- OpenCV
- PyTorch
- TensorFlow
- Tesseract OCR
- Google Cloud Text-to-Speech
- MoviePy
- PyQt6

## License

MIT License
