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

assertEquals () {
  if [ "$1" != "$2" ]; then
    echo "[FAILURE] $cmd"
	echo "   Expected: $2"
	echo "   but was: $1"
	fails=$(( 1 + $fails ))
  else
    echo "[SUCCESS] $cmd"
  fi
}


zonewithresources=$1

# Create a settings
cmd='python neoload test-settings --zone ${zonewithresources} --scenario some_scenario --naming-pattern "CLI-fastfail-\${runID}" create "Test settings CLI to run fastfail"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI to run fastfail"'
assertJsonEquals '.description' null
assertJsonEquals '.scenarioName' '"some_scenario"'
assertJsonEquals '.testResultNamingPattern' '"CLI-fastfail-${runID}"'
assertJsonEquals ".lgZoneIds.${zonewithresources}" 1
assertJsonEquals '.controllerZoneId' "\"${zonewithresources}\""


# Upload a project
cmd='python neoload project --path tests/neoload_projects/simpledemo.yml upload'
out=`eval $cmd`
assertJsonEquals '.projectName' '"NeoLoad-CLI-simpledemo"'
assertJsonEquals '.scenarios[0].scenarioName' '"simpledemo"'


# Run the test
cmd='python neoload run -d --scenario simpledemo'
out=`eval $cmd`
assertEquals "$?" '0'


# Fastfail
cmd='python neoload fastfail --max-failure 0 slas cur'
out=`eval $cmd > fastfail.log`
echo "[DONE]" $cmd "Write output to file fastfail.log"
echo ">>> You MUST check manually that the differences below are ONLY the dates !"
diff fastfail.log tests/integration/expected/fastfail.log
rm -f fastfail.log

# Delete the settings
cmd='python neoload test-settings delete'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI to run fastfail"'

exit $fails
