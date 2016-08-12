#!/bin/bash
CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# This is the script that generates the CombinedUnitTests dynamically.It takes the name of the exchange as the argument.
ScriptPath=$CUR_DIR/works
cd ScriptPath

if [[ "$1" != @(*[A-Z]*) ]]
then
    echo "Invalid Exchange name: $1, Exiting."
    exit 5
else
    echo "Valid Exchange" "$1"
fi

Var1="CombinedUnitTests"
Var2="_"
Var3=".py"
TestPlan=$ScriptPath/$Var1$Var2$1$Var3
echo "Creating the TestScript named $TestPlan"


#Attributes="Attributes"
#################### changes
#Datafile=$1$Attributes
Datafile=TestAttributes
echo "Using the Datafile named $Datafile"

#RawCombinedUnitTests.txt is the file that has the names of all the test cases that we plan to run 

testname_data=$ScriptPath/testname.dat

rm -f $testname_data
cut -d '.' -f1 $ScriptPath/RawCombinedUnitTests.txt > $testname_data


echo "from OmEngineState import OmEngineState" > "$TestPlan"
printf "\n">> "$TestPlan"
printf "import apolloTestUtilities\n">> "$TestPlan"
while read EachLine
do
echo  "import $EachLine" >> "$TestPlan"
done < $testname_data
printf "\n">> "$TestPlan"

echo "from $Datafile import $Datafile" >> "$TestPlan"
printf "\n">> "$TestPlan"
printf "def create(testSuiteName, engineStripeName, numTests): \n" >> "$TestPlan"
printf "\t\"this is the public interface, called by omsimulator.py\"\n" >> "$TestPlan"
printf "\ttestSuite = []\n">> "$TestPlan"
printf "\tengineState = OmEngineState(engineStripeName) \n" >> "$TestPlan"
printf "\tAtr = $Datafile(engineStripeName) \n" >> "$TestPlan"
printf "\tlogon = apolloTestUtilities.runLogon(engineState, testSuite)\n" >> "$TestPlan"
printf "\n">> "$TestPlan"

while read EachLine
do
printf "\ttestSuite.extend($EachLine.create(engineState, numTests, Atr.gettargetcompid(), Atr.getsendcompid(),Atr)) \n" >> "$TestPlan"
done < $testname_data

printf "\n">> "$TestPlan"
printf "\tlogout = apolloTestUtilities.runLogout(engineState, testSuite)\n" >> "$TestPlan"
printf "\treturn testSuite \n">> "$TestPlan"

#Changing the permission for the "$TestPlan" to a script .
chmod 755 "$TestPlan"
exit $?
