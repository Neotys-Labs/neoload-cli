#!/bin/bash

fails=0
uid=$1
zonewithresources=$2

assertJsonEquals () {
  if [ "$(echo $out | jq $1)" != "$2" ]; then
    echo "[FAILURE] [${0##*/}] $cmd"
	echo "   Expected: $2"
	echo "   but jq '$1' was: $(echo $out | jq $1)"
	fails=$(( 1 + $fails ))
  else
    echo "[SUCCESS] $cmd"
  fi
}

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


# Readme TL;DR command : Create a settings, upload project, run the test
cmd='python neoload test-settings --zone ${zonewithresources} --lgs 1 --scenario simpledemo --naming-pattern "CLI-\${runID}" createorpatch "Test settings CLI to run (readme) ${uid}" project --path tests/neoload_projects/simpledemo.yml upload "Test settings CLI to run (readme) ${uid}" run'
out=`eval $cmd`
assertEquals "$?" '0'

exit $fails
