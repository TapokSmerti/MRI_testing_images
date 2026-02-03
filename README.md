# DICOM Image Processor

## Overview

This project is a **command-line DICOM image processing tool** designed for basic MRI image analysis, including **signal and noise estimation** and **SNR calculation**.  
The script loads a DICOM file, automatically detects the region of interest (ROI), separates signal and background noise regions using morphological operations, and visualizes the results.

The output is a PNG image with **annotated contours and quantitative metrics**, suitable for quality control and exploratory analysis of medical images.

---

## Features

- Interactive **menu-driven CLI interface**
- File selection via **Tkinter GUI**
- DICOM image loading using **pydicom**
- Automatic ROI detection using **OpenCV contours**
- Signal and noise region separation
- Statistical analysis:
  - Mean
  - Standard deviation
  - Minimum / maximum intensity
  - Signal-to-Noise Ratio (SNR)
- Visualization with:
  - Inner (signal) contours
  - Outer (noise) contours
  - Overlayed text annotations
- Export of processed image as `.png`

---

## Processing Pipeline

1. Load DICOM file  
2. Normalize image intensity  
3. Binary thresholding  
4. Contour detection  
5. ROI mask construction  
6. Morphological operations  
   - Erosion → signal region  
   - Dilation → noise region  
7. Signal & noise statistics computation  
8. SNR calculation  
9. Visualization and result export  

---

## Example Output

The generated PNG image includes:
- Signal region contours (blue)
- Noise region contours (red)
- Signal statistics (left side)
- Noise statistics (right side)
- Flip angle and sequence name
- Computed SNR value

---
