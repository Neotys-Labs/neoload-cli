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


zonewithoutresources=$1

# Create a settings
cmd='python neoload test-settings --zone ${zonewithoutresources} --scenario simpledemo --naming-pattern "CLI-docker-\${runID}" create "Test settings CLI to run with docker resources"'
out=`eval $cmd`
assertJsonEquals '.name' '"Test settings CLI to run with docker resources"'
assertJsonEquals '.description' null
assertJsonEquals '.scenarioName' '"simpledemo"'
assertJsonEquals '.testResultNamingPattern' '"CLI-docker-${runID}"'
assertJsonEquals ".lgZoneIds.${zonewithoutresources}" 1
assertJsonEquals '.controllerZoneId' "\"${zonewithoutresources}\""


# Upload a project
cmd='python neoload project --path tests/neoload_projects/simpledemo.yml upload'
out=`eval $cmd`
assertJsonEquals '.projectName' '"NeoLoad-CLI-simpledemo"'
assertJsonEquals '.scenarios[0].scenarioName' '"simpledemo"'


# Deploy resources
cmd='python neoload docker prepare'
out=`eval $cmd`
assertEquals "$?" '0'
echo "[DONE]" $cmd $out

cmd='python neoload docker attach'
out=`eval $cmd`
assertEquals "$?" '0'
echo "[DONE]" $cmd $out


# Run the test
cmd='python neoload run'
out=`eval $cmd > run.log`
echo "[DONE]" $cmd "Write output to file run.log"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff run.log tests/integration/expected/run.log
rm -f run.log


# UnDeploy resources
cmd='python neoload docker detach'
out=`eval $cmd`
assertEquals "$?" '0'
echo "[DONE]" $cmd $out


# Forget the docker preparation
cmd='python neoload docker forget'
out=`eval $cmd`
assertEquals "$?" '0'
echo "[DONE]" $cmd $out

exit $fails
