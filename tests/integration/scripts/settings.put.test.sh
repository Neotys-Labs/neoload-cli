#!/bin/bash

fails=0

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


# Create
cmd='python neoload test-settings create "Test settings CLI put"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI put"'
assertJsonEquals '.scenarioName' null
assertJsonEquals '.description' null
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Put all fields
cmd='python neoload test-settings --rename "Test settings CLI patch2" --scenario newScenario --description "my desc"  --zone myZone --lgs myZone:3,myZone2:50 --naming-pattern "pattern" put'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI patch2"'
assertJsonEquals '.scenarioName' '"newScenario"'
assertJsonEquals '.description' '"my desc"'
assertJsonEquals '.lgZoneIds.defaultzone' null
assertJsonEquals '.lgZoneIds.myZone' 3
assertJsonEquals '.lgZoneIds.myZone2' 50
assertJsonEquals '.controllerZoneId' '"myZone"'
assertJsonEquals '.testResultNamingPattern' '"pattern"'


# Put only required fields
cmd='python neoload test-settings --rename "Test settings CLI put2" put'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI put2"'
assertJsonEquals '.scenarioName' '""'
assertJsonEquals '.description' '""'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.lgZoneIds.myZone' null
assertJsonEquals '.lgZoneIds.myZone2' null
assertJsonEquals '.controllerZoneId' '"defaultzone"'
assertJsonEquals '.testResultNamingPattern' '""'


# Delete
cmd='python neoload test-settings delete "Test settings CLI put2"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI put2"'

exit $fails
