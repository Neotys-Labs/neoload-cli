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
cmd='python neoload test-settings --zone ${zonewithresources} --scenario sanityScenario --naming-pattern "CLI-wait-\${runID}" create "Test settings CLI to wait ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI to wait ${uid}\""
assertJsonEquals '.description' null
assertJsonEquals '.scenarioName' '"sanityScenario"'
assertJsonEquals '.testResultNamingPattern' '"CLI-wait-${runID}"'
assertJsonEquals ".lgZoneIds.${zonewithresources}" 1
assertJsonEquals '.controllerZoneId' "\"${zonewithresources}\""


# Upload a project
cmd='python neoload project --path tests/neoload_projects/simpledemo.yml upload'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.projectName' '"NeoLoad-CLI-simpledemo"'
assertJsonEquals '.scenarios[0].scenarioName' '"simpledemo"'


# Run the test with detach
cmd='python neoload run --scenario simpledemo -d'
out=`eval $cmd`
assertEquals "$?" '0'
runningTestId=`echo $out | jq .resultId`
assertJsonEquals '.resultId' "${runningTestId}"


# Wait for the end of the test
cmd="python neoload wait ${runningTestId}"
sleep 2
out=`eval $cmd > wait.log`
assertEquals "$?" '0'
echo "[DONE]" $cmd "Write log to file wait.log"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff wait.log tests/integration/expected/run.log
rm -f waitlog


# TODO the following command does not find the test result (by its name) : python neoload wait "Name Of The Test"

exit $fails
