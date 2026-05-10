#!/bin/bash
set -e

echo "Installing Linux Media Player..."

TMP_DIR=$(mktemp -d)
cd $TMP_DIR
curl -sSL -o media_player.tar.gz https://audio.leokontakt.de/media_player.tar.gz
tar -xzf media_player.tar.gz

sudo mkdir -p /opt/mediaplayer
sudo cp media_player.py /opt/mediaplayer/
sudo cp run_player.sh /opt/mediaplayer/
sudo chmod +x /opt/mediaplayer/media_player.py

# Create launcher
sudo tee /usr/local/bin/mediaplayer > /dev/null << LAUNCHER
#!/bin/bash
/opt/mediaplayer/venv/bin/python3 /opt/mediaplayer/media_player.py "\$@"
LAUNCHER

sudo chmod +x /usr/local/bin/mediaplayer

echo "Setting up Python environment..."
sudo python3 -m venv /opt/mediaplayer/venv
sudo /opt/mediaplayer/venv/bin/pip install -q pygame opencv-python requests Pillow

rm -rf $TMP_DIR

echo "Installation complete!"
echo "Run 'mediaplayer' to start the app"
