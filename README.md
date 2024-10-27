# Navigation_Camera


Required Commands to ruun on terminal before running the files

## for Debian
  +sudo apt update
  +sudo apt install libzbar0

## For Mac
  brew install zbar
  
## After that RUN
  pip install opencv-python pyzbar

## verification
  python3 -c "from pyzbar.pyzbar import decode; print('ZBar installed successfully')"

## for Gifs, Run
  pip install pillow
