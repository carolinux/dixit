#!/bin/bash

# 1. Check if a directory was provided
if [ -z "$1" ]; then
    echo "Usage: sh script.sh <directory_name>"
    exit 1
fi

# 2. Set source and destination paths
# ${1%/} removes a trailing slash if the user included one
SRC_DIR="${1%/}"
DEST_DIR="${SRC_DIR}-compressed"

# 3. Create the output directory if it doesn't exist
mkdir -p "$DEST_DIR"

echo "Processing images from $SRC_DIR to $DEST_DIR..."

# 4. Loop through jpg and jpeg files (case insensitive)
for img in "${SRC_DIR}"/*.jpg; do
    # Check if files actually exist to avoid errors on empty folders
    [ -e "$img" ] || continue
    
    filename=$(basename "$img")
    
    # 5. The Magic: Resize to 50% and set quality to 60 (medium compression)
    convert "$img" -resize 50% -quality 60 "$DEST_DIR/$filename"
    
    echo "Compressed: $filename"
done

echo "Done! Check your files in $DEST_DIR"
