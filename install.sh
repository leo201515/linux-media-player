#!/bin/bash
# One-line install command for Linux Media Player
# Usage: curl -sSL https://audio.leokontakt.de/install.sh | bash

set -e

echo "Installing Linux Media Player..."

# Download files
curl -sSL -o /tmp/media_player.py https://audio.leokontakt.de/media_player.py
curl -sSL -o /tmp/run_player.sh https://audio.leokontakt.de/run_player.sh

# Install to /usr/local/bin
sudo cp /tmp/media_player.py /usr/local/bin/mediaplayer
sudo cp /tmp/run_player.sh /usr/local/bin/mediaplayer-launcher
sudo chmod +x /usr/local/bin/mediaplayer /usr/local/bin/mediaplayer-launcher

# Cleanup
rm -f /tmp/media_player.py /tmp/run_player.sh

echo "Installation complete!"
echo "Run 'mediaplayer' to start the app"
