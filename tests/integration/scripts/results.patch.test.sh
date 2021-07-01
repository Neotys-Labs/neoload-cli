#!/bin/bash

fails=0

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


# Ls
cmd='python neoload test-results ls "CLI-1"'
out=`eval $cmd`
assertEquals "$?" '0'
resultId=`echo $out | jq .id`
assertJsonEquals '.name' '"CLI-1"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'
assertJsonEquals '.externalUrl' '""'
assertJsonEquals '.externalUrlLabel' '""'


# Use
cmd='python neoload test-results use "CLI-1"'
out=`eval $cmd`
assertEquals "$?" '0'
echo $out
echo "[DONE] $cmd"


# Patch all fields
cmd='python neoload test-results --rename "SLA test renamed" --description "some desc" --quality-status FAILED --external-url http://url --external-url-label ext_label patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"SLA test renamed"'
assertJsonEquals '.description' '"some desc"'
assertJsonEquals '.qualityStatus' '"FAILED"'
assertJsonEquals '.externalUrl' '"http://url"'
assertJsonEquals '.externalUrlLabel' '"ext_label"'


# Patch without any change
cmd='python neoload test-results patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"SLA test renamed"'
assertJsonEquals '.description' '"some desc"'
assertJsonEquals '.qualityStatus' '"FAILED"'
assertJsonEquals '.externalUrl' '"http://url"'
assertJsonEquals '.externalUrlLabel' '"ext_label"'

# Patch with empty field to go back to the initial state
cmd='python neoload test-results --rename "CLI-1" --description "" --quality-status PASSED --external-url "" --external-url-label "" patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"CLI-1"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'
assertJsonEquals '.externalUrl' '""'
assertJsonEquals '.externalUrlLabel' '""'

exit $fails
