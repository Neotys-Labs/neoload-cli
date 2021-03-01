#!/bin/bash

if [ "$#" -ne 3 ]; then
  echo "Need 3 arguments and need to be launched from the root of the repo." >&2
  echo "Example : ./tests/integration/runAllScripts.sh https://nlwonprem253-wks-onprem.neotys.com/ abcdeftokentokentoken defaultzone" >&2
  echo "The URL must point at a NLWeb with a valid license installed, and at least 1 controller and 1 LG on the provided zone." >&2
  echo "The token must be luke on Jedi1 for internal stack" >&2
  exit 1
fi

fails=0
workspaceName='CLI'
runApiV2Tests=false
uid=$(date +%s)

if [ "$runApiV2Tests" = true ]; then
  # Test API V2 without workspaces
  python neoload login --url $1 $2
  tests/integration/scripts/run.test.sh $uid $3 ; fails=$(( $? + $fails ))
  tests/integration/scripts/run.fastfail.test.sh $uid $3 ; fails=$(( $? + $fails ))
  tests/integration/scripts/wait.test.sh $uid $3 ; fails=$(( $? + $fails ))
  tests/integration/scripts/run.oneliner.test.sh $uid $3 ; fails=$(( $? + $fails ))
  tests/integration/scripts/results.put.test.sh ; fails=$(( $? + $fails ))
  tests/integration/scripts/results.delete.test.sh ; fails=$(( $? + $fails ))
  tests/integration/scripts/settings.create.delete.test.sh $uid ; fails=$(( $? + $fails ))
  tests/integration/scripts/settings.patch.test.sh $uid ; fails=$(( $? + $fails ))
  tests/integration/scripts/settings.put.test.sh $uid ; fails=$(( $? + $fails ))
  tests/integration/scripts/zones.ls.test.sh $uid ; fails=$(( $? + $fails ))
  tests/integration/scripts/project.upload.test.sh $uid ; fails=$(( $? + $fails ))
  tests/integration/scripts/validate.test.sh ; fails=$(( $? + $fails ))

  echo "======  Cleanup test settings and test results  ======"
  if [ $fails -eq 0 ]; then
    tests/integration/scripts/cleanup.sh $uid $1 $2
  else
    echo "[WARNING] - Cleanup skipped because there is failures."
    echo "[WARNING] - To cleanup manually, run  ./tests/integration/scripts/cleanup.sh $uid [NLW api url] [your NLW token]"
  fi
  echo ""
fi



# Test API V3 with a particular workspace
python neoload login --workspace $workspaceName --url $1 $2
tests/integration/scripts/run.test.sh $uid $3 ; fails=$(( $? + $fails ))
tests/integration/scripts/run.fastfail.test.sh $uid $3 ; fails=$(( $? + $fails ))
tests/integration/scripts/run.oneliner.test.sh $uid $3 ; fails=$(( $? + $fails ))
tests/integration/scripts/wait.test.sh $uid $3 ; fails=$(( $? + $fails ))
tests/integration/scripts/results.put.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/results.delete.test.sh ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.create.delete.test.sh $uid ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.patch.test.sh $uid ; fails=$(( $? + $fails ))
tests/integration/scripts/settings.put.test.sh $uid ; fails=$(( $? + $fails ))
tests/integration/scripts/zones.ls.test.sh $uid ; fails=$(( $? + $fails ))
tests/integration/scripts/project.upload.test.sh $uid ; fails=$(( $? + $fails ))
tests/integration/scripts/validate.test.sh ; fails=$(( $? + $fails ))

echo "There are $fails failures"
echo ""

echo "======  Cleanup test settings and test results  ======"
if [ $fails -eq 0 ]; then
  tests/integration/scripts/cleanup.sh $uid $1 $2 $workspaceName
else
  echo "[WARNING] - Cleanup skipped because there is failures."
  echo "[WARNING] - To cleanup manually, run  ./tests/integration/scripts/cleanup.sh $uid [NLW api url] [your NLW token]"
fi
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