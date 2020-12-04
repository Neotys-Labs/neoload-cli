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
cmd='python neoload test-settings create "Test settings CLI"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI"'
assertJsonEquals '.description' null
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'
assertJsonEquals '.lgZoneIds.defaultzone' 1
assertJsonEquals '.controllerZoneId' '"defaultzone"'


# List
cmd='python neoload test-settings ls'
out=`eval $cmd`
assertJsonEquals '.[0].name' '"Test settings CLI"'


# Create a test to delete
cmd='python neoload test-settings --description "desc" --scenario "scenario1" --zone "myzone" --lgs 3 --naming-pattern "MyRunNumber\${runID}" create "Test settings CLI_2"'
out=`eval $cmd`
testToDeleteId=`echo $out | jq .id`
assertJsonEquals '.name' '"Test settings CLI_2"'
assertJsonEquals '.scenarioName' '"scenario1"'
assertJsonEquals '.description' '"desc"'
assertJsonEquals '.lgZoneIds.myzone' 3
assertJsonEquals '.controllerZoneId' '"myzone"'
assertJsonEquals '.testResultNamingPattern' '"MyRunNumber${runID}"'


# List
cmd='python neoload test-settings ls'
out=`eval $cmd`
assertJsonEquals '.[0].name' '"Test settings CLI_2"'


# Create all fields
cmd='python neoload test-settings --zone "myzone" create "Test settings CLI_3"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI_3"'
assertJsonEquals '.scenarioName' null
assertJsonEquals '.description' null
assertJsonEquals '.lgZoneIds.myzone' 1
assertJsonEquals '.controllerZoneId' '"myzone"'
assertJsonEquals '.testResultNamingPattern' '"#${runID}"'


# Delete
cmd='python neoload test-settings delete'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI_3"'


# Delete with name
cmd='python neoload test-settings delete "Test settings CLI"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI"'


# Delete with id
cmd="python neoload test-settings delete ${testToDeleteId}"
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI_2"'

exit $fails
