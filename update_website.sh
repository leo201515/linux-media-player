#!/bin/bash
# Run this with sudo: sudo bash /home/leo/viedio/update_website.sh

set -e

echo "Updating website files..."

cd /var/www/html

# Extract media_player.py and run_player.sh from tar.gz
tar -xzf media_player.tar.gz media_player.py run_player.sh
chmod 644 media_player.py run_player.sh

# Update install.sh
cat > install.sh << 'EOF'
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
mkdir -p /opt/mediaplayer
cp media_player.py /opt/mediaplayer/
cp run_player.sh /opt/mediaplayer/

# Create launcher
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
tee /usr/local/bin/mediaplayer > /dev/null << LAUNCHER
#!/bin/bash
INSTALL_DIR="/opt/mediaplayer"
export PYTHONPATH="\$INSTALL_DIR/venv/lib/python\$PYTHON_VERSION/site-packages:\$PYTHONPATH"
python3 "\$INSTALL_DIR/media_player.py" "\$@"
LAUNCHER

chmod +x /usr/local/bin/mediaplayer /opt/mediaplayer/media_player.py

# Setup venv and dependencies
echo "Setting up Python environment..."
python3 -m venv /opt/mediaplayer/venv 2>/dev/null || (apt-get update && apt-get install -y python3-venv && python3 -m venv /opt/mediaplayer/venv)
/opt/mediaplayer/venv/bin/pip install -q python-vlc requests

# Cleanup
rm -rf $TMP_DIR

echo "Installation complete!"
echo "Run 'mediaplayer' to start the app"
EOF

chmod 755 install.sh

echo "Website updated successfully!"
ls -la media_player.py run_player.sh install.sh
