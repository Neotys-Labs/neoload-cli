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


assertContains () {
  case "$1" in
    *"$2"*) echo "[SUCCESS] $cmd contains [$2]" ;;
    *)
      echo "[FAILURE] [${0##*/}] $cmd"
      echo "   Output: $1"
      echo "   does not contain: $2"
      fails=$(( 1 + $fails ))
      ;;
  esac
}


cmd='python neoload validate tests/neoload_projects/example_1'
out=`eval $cmd`
assertEquals "$?" '0'
assertContains "$out" 'All yaml files underneath the path provided are valid against NeoLoad DSL schema version 3.0.'
assertContains "$out" 'You are using NeoLoad DSL schema version 3.0'
assertContains "$out" 'schemaVersion:'


cmd='python neoload validate tests/neoload_projects/example_1/default.yaml'
out=`eval $cmd`
assertEquals "$?" '0'
assertContains "$out" 'Yaml file is valid against NeoLoad DSL schema version 3.0.'
assertContains "$out" 'You are using NeoLoad DSL schema version 3.0'
assertContains "$out" 'schemaVersion:'


cmd='python neoload validate tests/neoload_projects/invalid_to_schema.yaml'
out=`eval $cmd`
assertEquals "$?" '1'

exit $fails
