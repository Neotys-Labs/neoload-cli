#!/bin/bash

fails=0
uid=$1

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


# Create the test with "createorpatch"
cmd='python neoload test-settings createorpatch "Test settings CLI patch ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch ${uid}\""
assertJsonEquals '.scenarioName' null
assertJsonEquals '.description' null
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Patch the test with "createorpatch". Nothing should be modified
cmd='python neoload test-settings createorpatch "Test settings CLI patch ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch ${uid}\""
assertJsonEquals '.scenarioName' '""'
assertJsonEquals '.description' '""'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Patch name scenario description pattern
cmd='python neoload test-settings --rename "Test settings CLI patch2 ${uid}" --scenario newScenario --description "my desc" --naming-pattern "pattern" patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch2 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Patch lgs
cmd='python neoload test-settings --lgs 3 patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch2 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.defaultzone' 3
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Patch lgs
cmd='python neoload test-settings --lgs zone:3,zone2:4 patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch2 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.zone' 3
assertJsonEquals '.lgZoneIds.zone2' 4
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Patch zone
cmd='python neoload test-settings --zone myZone patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch2 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.zone' 3
assertJsonEquals '.lgZoneIds.zone2' 4
assertJsonEquals '.lgZoneIds.myZone' null
assertJsonEquals '.controllerZoneId' '"myZone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Patch name
cmd='python neoload test-settings --rename "Test settings CLI patch3 ${uid}" patch'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch3 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.zone' 3
assertJsonEquals '.lgZoneIds.zone2' 4
assertJsonEquals '.lgZoneIds.myZone' null
assertJsonEquals '.controllerZoneId' '"myZone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Delete
cmd='python neoload test-settings delete "Test settings CLI patch3 ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch3 ${uid}\""

exit $fails
