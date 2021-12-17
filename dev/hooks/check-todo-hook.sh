#!/bin/bash

grep --text --recursive --exclude=.pre-commit-config.yaml --exclude=check-todo-hook.sh --exclude=explore.py --exclude-dir=.git --exclude-dir=coverage --exclude-dir=node_modules --files-with-matches --color 'TODO' .
status=$?

if [ $status -ne 1 ]; then
    echo "Please, delete TODO statements"
    exit 1
else
    exit 0
fi
