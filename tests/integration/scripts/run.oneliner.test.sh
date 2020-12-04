#!/bin/bash

fails=0

assertEquals () {
  if [ "$1" != "$2" ]; then
    echo "[FAILURE] $cmd"
	echo "   Expected: $2"
	echo "   but was: $1"
	fails=$(( 1 + $fails ))
  else
    echo "[SUCCESS] $cmd"
  fi
}


zonewithresources=$1

# Readme TL;DR command : Create a settings, upload project, run the test
cmd='python neoload test-settings --zone ${zonewithresources} --lgs 1 --scenario simpledemo --naming-pattern "CLI-\${runID}" createorpatch "Test settings CLI to run (readme)" project --path tests/neoload_projects/simpledemo.yml upload "Test settings CLI to run (readme)" run'
out=`eval $cmd`
assertEquals "$?" '0'

# Delete
cmd='python neoload test-settings delete'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI to run (readme)"'

exit $fails
