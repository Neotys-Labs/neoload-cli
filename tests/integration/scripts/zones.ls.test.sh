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
cmd='python neoload zones'
out=`eval $cmd`
assertEquals "$?" '0'
firstZoneId=`echo $out | jq .[0].id`
firstZoneName=`echo $out | jq .[0].name`
firstZoneType=`echo $out | jq .[0].type`


# Ls one zone by id
cmd="python neoload zones ${firstZoneId}"
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].id' "${firstZoneId}"
assertJsonEquals '.[0].name' "${firstZoneName}"
assertJsonEquals '.[0].type' "${firstZoneType}"


# Ls one zone by name
cmd="python neoload zones ${firstZoneName}"
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].id' "${firstZoneId}"
assertJsonEquals '.[0].name' "${firstZoneName}"
assertJsonEquals '.[0].type' "${firstZoneType}"


# Ls static zones
cmd="python neoload zones --static"
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].type' '"STATIC"'


# Ls dynamic zones
cmd="python neoload zones --dynamic"
out=`eval $cmd`
assertEquals "$?" '0'
assertJsonEquals '.[0].type' '"DYNAMIC"'

exit $fails
