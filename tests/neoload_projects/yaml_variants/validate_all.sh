set +e

output=""
lastrun=""
function runthis(){
  lastrun=$1
  output=`$1  &> /dev/null`
}
error_if_errored(){
  if [ "$?" -ne "0" ]; then
    echo "POSITIVE TEST: shouldn't have failed, but did"
    echo $lastrun
    output=`$lastrun`
    echo $output
    return
  else
    return 1
  fi
}
error_if_should_have_errored_but_didnt(){
  if [ "$?" -eq "0" ]; then
    echo "NEGATIVE TEST: should have failed, but didn't"
    echo $lastrun
    output=`$lastrun`
    echo $output
    return
  else
    return 1
  fi
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

for i in $(ls -1 -d "$DIR/"*.yaml); do
  echo "Running $i"
  runthis "neoload validate $i"
  if [[ "$i" =~ .*/valid_.* ]]; then
    if error_if_errored; then exit 5500; fi
  else
    if error_if_should_have_errored_but_didnt; then exit 5500; fi
  fi
done


runthis "neoload validate $DIR/improperly_indented.yaml"
if error_if_should_have_errored_but_didnt; then exit 5500; fi

runthis "neoload validate $DIR/missing_request_url.yaml"
if error_if_should_have_errored_but_didnt; then exit 5500; fi

runthis "neoload validate $DIR/no_scenario_duration.yaml"
if error_if_should_have_errored_but_didnt; then exit 5500; fi

runthis "neoload validate $DIR/user_path_invalid_elements.yaml"
if error_if_should_have_errored_but_didnt; then exit 5500; fi

runthis "neoload validate $DIR/user_path_no_actions_container.yaml"
if error_if_should_have_errored_but_didnt; then exit 5500; fi

echo "All POSITIVE and NEGATIVE validations passed."
set -e
