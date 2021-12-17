#!/bin/bash

pipenv run coverage report --rcfile=dev/py/coverage/.coveragerc --fail-under=50
status=$?

pipenv run coverage erase

exit $status
