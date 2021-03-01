#!/bin/bash

fails=0

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


# Ls
cmd='python neoload test-results ls "CLI-1"'
out=`eval $cmd`
assertEquals "$?" '0'
resultId=`echo $out | jq .id`
assertJsonEquals '.name' '"CLI-1"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'


# Use
cmd='python neoload test-results use "CLI-1"'
out=`eval $cmd`
assertEquals "$?" '0'
echo $out
echo "[DONE] $cmd"


# Put all fields
cmd='python neoload test-results --rename "SLA test renamed" --description "some desc" --quality-status FAILED put'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"SLA test renamed"'
assertJsonEquals '.description' '"some desc"'
assertJsonEquals '.qualityStatus' '"FAILED"'


# Put only required fields
cmd='python neoload test-results --rename "SLA test renamed2" --quality-status PASSED put'
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.id' "${resultId}"
assertJsonEquals '.name' '"SLA test renamed2"'
assertJsonEquals '.description' '""'
assertJsonEquals '.qualityStatus' '"PASSED"'


# Summary
cmd='python neoload test-results summary'
out=`eval $cmd > summary.txt`
assertEquals "$?" '0'
echo ""
echo "[DONE]" $cmd "Write output to file summary.txt"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff summary.txt tests/integration/expected/summary.txt
echo ""
rm -f summary.txt


# Junit-SLA
cmd='python neoload test-results junitsla'
out=`eval $cmd`
assertEquals "$?" '0'
echo ""
echo "[DONE]" $cmd "Write output to file junit-sla.xml"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff junit-sla.xml tests/integration/expected/junit-sla.xml
echo ""
rm -f junit-sla.xml


# Junit-SLA with file name
cmd='python neoload test-results --junit-file junit.xml junitsla'
out=`eval $cmd`
assertEquals "$?" '0'
echo ""
echo "[DONE]" $cmd "Write output to file junit.xml"
echo ">>> You MUST check manually that the differences below are ONLY IDs and numbers !!"
diff junit.xml tests/integration/expected/junit-sla.xml
echo ""
rm -f junit.xml

exit $fails
