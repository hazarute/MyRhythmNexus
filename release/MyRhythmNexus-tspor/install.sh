#!/bin/sh
APPDIR=${XDG_CONFIG_HOME:-$HOME/.config}/MyRhythmNexus
mkdir -p "$APPDIR"
cp "$(dirname "$0")/MyRhythmNexus_v1.0.3.exe" "$APPDIR/MyRhythmNexus_v1.0.3.exe"
cp "$(dirname "$0")/config.json" "$APPDIR/config.json"
echo 'Kurulum tamamlandi.'
