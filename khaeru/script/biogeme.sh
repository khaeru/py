#!/bin/sh
usage () {
  if [ -n "$1" ];
  then
    echo "$(basename $0): cannot access $1: No such file"
  fi
  cat <<-EOF
	Usage: $(basename $0) MODEL.mod DATA

	Run biogeme in a temporary directory (under \$TMPDIR or /tmp) to control
	its outputs. If an output file like MODEL.html exists, biogeme's default
	behaviour is to create MODEL~1.html, MODEL~2.html, etc. With biogeme.sh,
	these files are *overwritten* in the current directory.

	ALSO

	- Files listed in the IGNORE variable (see source) are discarded.
	- The LaTeX output in MODEL.tex is edited to delete the line:

	    \end{document}
	
	  …which causes problems when including this file in another LaTeX
	  document using \input{}.
	- The .par file in the current directory (either MODEL.par or
	  default.par) is used if it exists; or if none exists, the default.par
	  created by biogeme is saved.
	- summary.html in the current directory is updated, if it exists.

	DIRECTORIES

	If MODEL.mod is in a different directory, biogeme creates some output
	files (e.g. MODEL.html) in the same directory as MODEL.mod, and other
	output files (e.g. summary.html) in the current directory. In contrast,
	biogeme.sh creates all output files in the current directory.

EOF
  exit 1
}

# Create a temporary directory
ORIGIN=`pwd`
DIR=`mktemp --tmpdir -d biogeme.XXX`

# Symlink the model file into the temporary directory
if [ -f "$1" ];
then
  MODFILE=`realpath $1`
  MODEL=`basename -s .mod $1`
  ln -s $MODFILE $DIR/
else
  usage $1
fi

IGNORE="*.F12
  *.res
  *.sta
  $MODEL.html
  __specFile.debug
  model.debug
  parameters.out
  hess.lis
  hessian.lis"

# Store the path to the data file
if [ -f "$2" ];
then
  DATA=`realpath $2`
else
  usage $2
fi

# Check for a .par file
if [ -f "$MODEL.par" ];
then
  PARFILE=`realpath $MODEL.par`
elif [ -f "default.par" ];
then
  PARFILE=`realpath default.par`
fi

if [ -n "$PARFILE" ];
then
  ln -s $PARFILE $DIR/
fi

# Check for a summary file
if [ -f "summary.html" ];
then
  ln -s `realpath summary.html` $DIR/
fi

ls -l $DIR

# Run biogeme
cd $DIR
biogeme $MODEL $DATA

FILES=`find $DIR -type f $(printf "! -name %s " $(echo $IGNORE | tr ' ' '\n'))`

if [ -f "$MODEL.tex" ];
then
  sed -i '/\\end{document}/d' $MODEL.tex
fi

cp $FILES $ORIGIN

cd $ORIGIN

rm -r $DIR
