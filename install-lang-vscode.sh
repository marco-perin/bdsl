#!/bin/sh

# Script to install the BDSL language extension for Visual Studio Code.
# That needs to be compiled first in the subfolder. 

path="editor/vscode/bdsl-lang/bdsl-lang-0.0.2.vsix"
code --install-extension $path
rm $path
