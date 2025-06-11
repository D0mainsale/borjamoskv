# Borja Moskv

This repository contains various data files and assets. A new Python script `image_scaler.py` provides a simple command-line interface for scaling images using the Pillow library.

## Usage

```bash
python3 image_scaler.py input.jpg output.jpg --scale 0.5
```

You can also specify a target width and/or height instead of a scale factor:

```bash
python3 image_scaler.py input.jpg output.jpg --width 100 --height 200
```

Ensure you have the Pillow package installed:

```bash
pip install pillow
```
