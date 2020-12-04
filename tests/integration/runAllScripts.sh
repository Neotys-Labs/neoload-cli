#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Need 2 arguments and need to be launched from the root of the repo." >&2
  echo "Example : ./tests/integration/runAllScripts.sh https://nlwonprem253-wks-onprem.neotys.com/ abcdeftokentokentoken" >&2
  echo "The URL must point at a NLWeb with a valid license installed, and at least 1 controller and 1 LG on the default zone." >&2
  echo "The token must be luke on Jedi1" >&2
  exit 1
fi

fails=0

python neoload login --url $1 $2
tests/integration/scripts/run.test.sh FGN4h ; fails=$(( $? + $fails ))
tests/integration/scripts/run.fastfail.test.sh FGN4h ; fails=$(( $? + $fails ))
#tests/integration/scripts/run.docker.test.sh cuPd2 ; fails=$(( $? + $fails ))
tests/integration/scripts/wait.test.sh FGN4h ; fails=$(( $? + $fails ))
tests/integration/scripts/run.oneliner.test.sh FGN4h ; fails=$(( $? + $fails ))
tests/integration/scripts/results.put.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/results.delete.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.create.delete.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.patch.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.put.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/zones.ls.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/project.upload.test.sh ; fails=$(( $? + $fails ))


# With another workspace
python neoload login --workspace CLI --url $1 $2
tests/integration/scripts/run.test.sh FGN4h ; fails=$(( $? + $fails ))
tests/integration/scripts/run.fastfail.test.sh FGN4h ; fails=$(( $? + $fails ))
#tests/integration/scripts/run.docker.test.sh cuPd2 ; fails=$(( $? + $fails ))
tests/integration/scripts/wait.test.sh FGN4h ; fails=$(( $? + $fails ))
tests/integration/scripts/results.put.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/results.delete.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.create.delete.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.patch.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.put.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/zones.ls.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/project.upload.test.sh ; fails=$(( $? + $fails ))


echo "There are $fails failures"
echo ""

echo "======  Manually check that these commands does not throw an error  ======"
echo "_____________________________"
echo "Status is:"
python neoload status
echo "_____________________________"
echo "Logout:"
python neoload logout
echo "_____________________________"
echo "Status when logged out is:"
python neoload status
echo "_____________________________"
echo "Version is:"
python neoload --version
echo "_____________________________"
echo "Help is:"
python neoload --help

exit $fails