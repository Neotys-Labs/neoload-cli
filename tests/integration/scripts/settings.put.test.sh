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


# Create
cmd='python neoload test-settings create "Test settings CLI put ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI put ${uid}\""
assertJsonEquals '.scenarioName' null
assertJsonEquals '.description' null
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Put all fields
cmd='python neoload test-settings --rename "Test settings CLI patch2 ${uid}" --scenario newScenario --description "my desc"  --zone myZone --lgs myZone:3,myZone2:50 --naming-pattern "pattern" put'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI patch2 ${uid}\""
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.defaultzone' null
assertJsonEquals '.lgZoneIds.myZone' 3
assertJsonEquals '.lgZoneIds.myZone2' 50
assertJsonEquals '.controllerZoneId' '"myZone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Put only required fields
cmd='python neoload test-settings --rename "Test settings CLI put2 ${uid}" put'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI put2 ${uid}\""
assertJsonEquals '.scenarioName' '""'
assertJsonEquals '.description' '""'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.lgZoneIds.myZone' null
assertJsonEquals '.lgZoneIds.myZone2' null
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '""'


# Delete
cmd='python neoload test-settings delete "Test settings CLI put2 ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI put2 ${uid}\""

exit $fails
