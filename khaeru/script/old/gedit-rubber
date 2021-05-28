#!/bin/sh
# (comments at bottom)

# [Gedit Tool]
# Comment=rubber
# Name=Rubber
# Shortcut=<Control><Alt>1
# Languages=latex
# Applicability=all
# Output=output-panel
# Input=nothing
# Save-files=document

TEXINPUTS=~/Projects/latex-templates

RESULT_URI=`echo $GEDIT_CURRENT_DOCUMENT_URI | sed "s/.tex/.pdf/"`
RESULT_PATH=`echo $GEDIT_CURRENT_DOCUMENT_PATH | sed "s/.tex/.pdf/"`

rubber -dfs -n -1 -W all --inplace --texpath=$TEXINPUTS "$GEDIT_CURRENT_DOCUMENT_PATH"
# if the -z flag is passed, open the gzipped output
if [ -x "$RESULT_URI.gz" ]; then
  gnome-open "$RESULT_URI.gz"
else
  gnome-open "$RESULT_URI"
fi

# LaTeX compile script for the gedit plugin 'External Tools'
#   Copyright © 2010 Paul Kishimoto <mail@paul.kishimoto.name>
#   Made available under the GPLv3 (http://www.gnu.org/licenses/gpl-3.0.html)
#
# Requires the Ubuntu packages 'gedit-latex-plugin' and 'rubber'.
#
# There is a LaTeX plugin for gedit that you may want to use instead:
#   http://www.michaels-website.de/gedit-latex-plugin/
# This script simply runs your files through rubber. To use, create a symlink
# to this file from within ~/.gnome2/gedit/tools/ . You can edit the script or
# change the settings below using the interface to the 'External Tools' plugin:
# click Tools → Manage External Tools... from within gedit.
