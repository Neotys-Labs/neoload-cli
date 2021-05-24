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
cmd='python neoload run --scenario simpledemo --external-url "https://jenkins/1234" --external-url-label "Jenkins build 1234"'
out=`eval $cmd > run.log`
assertEquals "$?" '0'
echo "[DONE]" $cmd "Write output to file run.log"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff run.log tests/integration/expected/run.log
rm -f run.log

# Check the result
cmd='python neoload test-results ls "CLI-1"'
out=`eval $cmd`
assertEquals "$?" '0'
resultId=`echo $out | jq .id`
assertJsonEquals '.name' '"CLI-1"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'
assertJsonEquals '.externalUrl' '"https://jenkins/1234"'
assertJsonEquals '.externalUrlLabel' '"Jenkins build 1234"'

# Patch with empty external URL to go back to the initial state
cmd='python neoload test-results --external-url "" --external-url-label "" patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"CLI-1"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'
assertJsonEquals '.externalUrl' '""'
assertJsonEquals '.externalUrlLabel' '""'


exit $fails
