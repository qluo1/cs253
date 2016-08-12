#!/bin/bash
export PYTHONPATH=..
python <<ENDFACE
import os
import os.path
import pprint
import ast
import curses                                                                
from curses import panel 

script_dir = 'tests'
if not os.path.isdir(script_dir):
    print("You need to be in the TestCases directory")
    exit(1)

env = os.environ['ENV']

if not env in ['PME', 'PPE', 'QAE']:
    print('ENV should contain a valid environment name')
    exit(1)
test_files = []
fp = open('testRunner/setup/tests_by_env', 'r')
for line in fp:
    line = line.strip()
    if not line.startswith('#') and not line == "":
        parts = line.split(':')
        test_filename = parts[0]
        test_filename = test_filename.strip()
        test_files.append(test_filename)

for test_file in test_files:
    test_path = script_dir + '/om2/' + test_file
    if not os.path.isfile(test_path):
        print("error:File [" + test_path + "] does not exist")
        exit(1)
    IH = open(test_path, 'r')
    test_source = IH.read()
    IH.close()
    tree = ast.parse(test_source)
    for item in tree.body:
        if isinstance(item, ast.FunctionDef):
            function_name = item.name
            if function_name.startswith("test_"):
                print test_file, function_name
            
        if isinstance(item, ast.ClassDef):
            class_name = item.name
            if class_name.startswith("Test_"):
                for sub_item in item.body:
                    if isinstance(sub_item, ast.FunctionDef):
                        function_name = sub_item.name
                        if function_name.startswith("test_"):
                            print test_file, class_name, function_name

ENDFACE
