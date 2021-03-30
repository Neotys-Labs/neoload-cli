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


cmd='python neoload validate tests/neoload_projects/example_1'
out=`eval $cmd`
assertEquals "$?" '0'
assertEquals "$out" 'All yaml files underneath the path provided are valid.'


cmd='python neoload validate tests/neoload_projects/example_1/default.yaml'
out=`eval $cmd`
assertEquals "$?" '0'
assertEquals "$out" 'Yaml file is valid.'


cmd='python neoload validate tests/neoload_projects/invalid_to_schema.yaml'
out=`eval $cmd`
assertEquals "$?" '1'

exit $fails
