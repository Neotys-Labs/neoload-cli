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



# Create a settings
cmd='python neoload test-settings --zone ${zonewithresources} --scenario some_scenario --naming-pattern "CLI-\${runID}" create "Test settings CLI to run ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI to run ${uid}\""
assertJsonEquals '.description' null
assertJsonEquals '.scenarioName' '"some_scenario"'
assertJsonEquals '.testResultNamingPattern' '"CLI-${runID}"'
assertJsonEquals ".lgZoneIds.${zonewithresources}" 1
assertJsonEquals '.controllerZoneId' "\"${zonewithresources}\""


# Upload a project
cmd='python neoload project --path tests/neoload_projects/simpledemo.yml upload'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.projectName' '"NeoLoad-CLI-simpledemo"'
assertJsonEquals '.scenarios[0].scenarioName' '"simpledemo"'


# Run the test
cmd='python neoload run --scenario simpledemo'
out=`eval $cmd > run.log`
assertEquals "$?" '0'
echo "[DONE]" $cmd "Write output to file run.log"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff run.log tests/integration/expected/run.log
rm -f run.log

exit $fails
