#!/bin/sh

# Check if vsce is installed
if ! command -v vsce &> /dev/null
then
    echo "vsce could not be found, please install it first."
    exit 1
fi

# Pack the VS Code extension
vsce package

echo "VS Code extension has been packed successfully."