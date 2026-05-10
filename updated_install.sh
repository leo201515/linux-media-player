#!/bin/bash
# One-line install command for Linux Media Player
# Usage: curl -sSL https://audio.leokontakt.de/install.sh | bash

set -e

echo "Installing Linux Media Player..."

# Download and extract the full package
TMP_DIR=$(mktemp -d)
cd $TMP_DIR
curl -sSL -o media_player.tar.gz https://audio.leokontakt.de/media_player.tar.gz
tar -xzf media_player.tar.gz

# Install to /opt/mediaplayer
sudo mkdir -p /opt/mediaplayer
sudo cp media_player.py /opt/mediaplayer/
sudo cp run_player.sh /opt/mediaplayer/

# Create launcher
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
sudo tee /usr/local/bin/mediaplayer > /dev/null << EOF
#!/bin/bash
INSTALL_DIR="/opt/mediaplayer"
export PYTHONPATH="\$INSTALL_DIR/venv/lib/python\$PYTHON_VERSION/site-packages:\$PYTHONPATH"
python3 "\$INSTALL_DIR/media_player.py" "\$@"
EOF

sudo chmod +x /usr/local/bin/mediaplayer /opt/mediaplayer/media_player.py

# Setup venv and dependencies
echo "Setting up Python environment..."
sudo python3 -m venv /opt/mediaplayer/venv 2>/dev/null || (sudo apt-get update && sudo apt-get install -y python3-venv && sudo python3 -m venv /opt/mediaplayer/venv)
sudo /opt/mediaplayer/venv/bin/pip install -q python-vlc requests

# Cleanup
rm -rf $TMP_DIR

echo "Installation complete!"
echo "Run 'mediaplayer' to start the app"
