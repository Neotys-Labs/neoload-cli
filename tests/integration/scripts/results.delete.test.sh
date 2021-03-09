#!/bin/bash

fails=0

assertEquals () {
  if [ "$1" != "$2" ]; then
    echo "[FAILURE] [${0##*/}] $cmd"
	echo "   Expected: $2"
	echo "   but was: $1"
	fails=$(( 1 + $fails ))
  else
    echo "[SUCCESS] $cmd"
  fi
}


# Use
cmd='python neoload test-results use "CLI-wait-1"'
out=`eval $cmd`
assertEquals "$?" '0'
echo $out
echo "[DONE] $cmd"


# Delete
cmd='python neoload test-results delete'
out=`eval $cmd`
assertEquals "$?" '0'
echo $out
echo "[DONE] $cmd"

exit $fails
