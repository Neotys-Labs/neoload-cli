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
cmd='python neoload test-settings create "Test settings CLI ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI ${uid}\""
assertJsonEquals '.description' null
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'


# List
cmd='python neoload test-settings ls'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].name' "\"Test settings CLI ${uid}\""


# Create a test to delete
cmd='python neoload test-settings --description "desc" --scenario "scenario1" --zone "myzone" --lgs 3 --naming-pattern "MyRunNumber\${runID}" create "Test settings CLI_2 ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
testToDeleteId=`echo $out | jq .id`
assertJsonEquals '.name' "\"Test settings CLI_2 ${uid}\""
assertJsonEquals '.scenarioName' '"scenario1"'
assertJsonEquals '.description' '"desc"'
assertJsonEquals '.lgZoneIds.myzone' 3
assertJsonEquals '.controllerZoneId' '"myzone"'
assertJsonEquals '.testResultNamingPattern' '"MyRunNumber${runID}"'


# List
cmd='python neoload test-settings ls'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].name' "\"Test settings CLI_2 ${uid}\""


# Create all fields
cmd='python neoload test-settings --zone "myzone" create "Test settings CLI_3 ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI_3 ${uid}\""
assertJsonEquals '.scenarioName' null
assertJsonEquals '.description' null
assertJsonEquals '.lgZoneIds.myzone' 1
assertJsonEquals '.controllerZoneId' '"myzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Delete
cmd='python neoload test-settings delete'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI_3 ${uid}\""


# Delete with name
cmd='python neoload test-settings delete "Test settings CLI ${uid}"'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI ${uid}\""


# Delete with id
cmd="python neoload test-settings delete ${testToDeleteId}"
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.name' "\"Test settings CLI_2 ${uid}\""

exit $fails
