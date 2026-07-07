@echo off
Title Downloading Modules...
python -m pip install -r requirements.txt
echo ------------------------------------------------------------------------
python -c "import cv2; print(cv2.__version__); print(hasattr(cv2, 'groupRectangles'))"
echo Script reached end. If correctly done last 2 line says 4.xx.X TRUE, if not, fix it.
pause