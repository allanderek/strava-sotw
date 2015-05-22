#! /bin/sh

TEST_COMMAND="python manage.py test_all"

if [ "$1" == "coverage" ]
then
TEST_COMMAND="python manage.py coverage"
fi

echo $TEST_COMMAND

test_python(){
    venv=testvenv$1
    rm -fr ../$venv
    source setup.sh $1 $venv
    $TEST_COMMAND
    test_result=$?
    deactivate
    rm -fr ../$venv
    return $test_result
}

test_series() {
    for version in "$@"
    do
        test_python $version
        if [[ $? != 0 ]]
        then
            echo Tests failed for Python ${PYTHONVERSION}
            return 1
        fi
    done
}

test_series 3.4 2.7
