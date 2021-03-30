#!/bin/bash
# First Parameter is The uid of the url
# Second Parameter is Neoload API URL
# Third parameter is Neoload API Token
# Fourth parameter is the workspace name (or empty for default workspace)

fails=0
uid=$1

assertJsonEquals () {
  if [ "$(echo $out | jq $1)" != "$2" ]; then
    echo "[FAILURE] $cmd"
	echo "   Expected: $2"
	echo "   but jq '$1' was: $(echo $out | jq $1)"
	fails=$(( 1 + $fails ))
  else
    echo "[SUCCESS] $cmd"
  fi
}

if [ "$#" -lt 4 ]; then
  python neoload login --url $2 $3
else
  python neoload login --workspace $4 --url $2 $3
fi


# Delete the settings and associated results
cmd='python neoload test-settings delete "Test settings CLI to wait ${uid}"'
out=`eval $cmd`
assertJsonEquals '.name' "\"Test settings CLI to wait ${uid}\""


cmd='python neoload test-settings delete "Test settings CLI for project ${uid}"'
out=`eval $cmd`
assertJsonEquals '.name' "\"Test settings CLI for project ${uid}\""


cmd='python neoload test-settings delete "Test settings CLI to run ${uid}"'
out=`eval $cmd`
assertJsonEquals '.name' "\"Test settings CLI to run ${uid}\""


cmd='python neoload test-settings delete "Test settings CLI to run (readme) ${uid}"'
out=`eval $cmd`
assertJsonEquals '.name' "\"Test settings CLI to run (readme) ${uid}\""


cmd='python neoload test-settings delete "Test settings CLI to run fastfail ${uid}"'
out=`eval $cmd`
assertJsonEquals '.name' "\"Test settings CLI to run fastfail ${uid}\""


exit $fails
