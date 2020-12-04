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


# Create a settings
cmd='python neoload test-settings create "Test settings CLI for project"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI for project"'
assertJsonEquals '.description' null


# Upload zip
cmd='python neoload project --path tests/neoload_projects/example_1.zip upload'
out=`eval $cmd`
assertJsonEquals '.projectName' '"NeoLoad-CLI-example-2_0"'
assertJsonEquals '.asCodeFiles[0].path' '"example_1/default.yaml"'
assertJsonEquals '.asCodeFiles[0].includes[0]' '"paths/geosearch_get.yaml"'
assertJsonEquals '.asCodeFiles[1].path' '"example_1/paths/geosearch_get.yaml"'
assertJsonEquals '.scenarios[0].scenarioName' '"sanityScenario"'
assertJsonEquals '.scenarios[0].scenarioSource' '"example_1/default.yaml"'
assertJsonEquals '.scenarios[1].scenarioName' '"slaMinScenario"'
assertJsonEquals '.scenarios[2].scenarioName' '"fullTest"'


# Upload yml
cmd='python neoload project --path tests/neoload_projects/simpledemo.yml upload'
out=`eval $cmd`
assertJsonEquals '.projectName' '"NeoLoad-CLI-simpledemo"'
assertJsonEquals '.scenarios[0].scenarioName' '"simpledemo"'
assertJsonEquals '.asCodeFiles[0].path' '"simpledemo.yml"'
assertJsonEquals '.scenarios[0].scenarioSource' '"simpledemo.yml"'


# Upload folder
cmd='python neoload project --path tests/neoload_projects/example_1 upload'
out=`eval $cmd`
assertJsonEquals '.projectName' '"NeoLoad-CLI-example-2_0"'
assertJsonEquals '.asCodeFiles[0].path' '"default.yaml"'
assertJsonEquals '.asCodeFiles[0].includes[0]' '"paths/geosearch_get.yaml"'
assertJsonEquals '.asCodeFiles[1].path' '"paths/geosearch_get.yaml"'
assertJsonEquals '.scenarios[0].scenarioName' '"sanityScenario"'
assertJsonEquals '.scenarios[0].scenarioSource' '"default.yaml"'
assertJsonEquals '.scenarios[1].scenarioName' '"slaMinScenario"'
assertJsonEquals '.scenarios[2].scenarioName' '"fullTest"'


# Delete
cmd='python neoload test-settings delete'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI for project"'

exit $fails
