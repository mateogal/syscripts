# Wordlist/Dictionary generator
# This script is part of (https://github.com/mateogal/Syscripts)

#!/bin/bash

while getopts :p:o:r:s:h flag; do
    case "${flag}" in
    o) output=${OPTARG} ;;
    r) range=${OPTARG} ;;
    s) string=${OPTARG} ;;
    p)
        if [ "${OPTARG}" != "start" ] && [ "${OPTARG}" != "end" ]; then
            echo "Invalid value for position."
            exit 1
        fi
        position=${OPTARG}
        ;;
    h)
        echo ""
        echo "Required options:"
        echo ""
        echo "-r    (Password length range Ex. 8-15)"
        echo "-s    (Initial string to generate combinations)"
        echo "-p    (Position of the initial string [start/end])"
        echo "-o    (Output filename)"
        echo ""
        echo "Example: makeDict.sh -r 8-11 -s Testing -p end"
        echo ""
        echo "Output:"
        echo "XTesting"
        echo "XXTesting"
        echo "XXXTesting"
        echo "XXXXTesting"
        ;;
    :)
        echo "Option -${OPTARG} requires an argument."
        exit 1
        ;;
    ?)
        echo "Invalid option: -${OPTARG}."
        exit 1
        ;;
    esac
done

if [ -z $output ] || [ -z $range ] || [ -z $string ] || [ -z $position ]; then
    echo ""
    echo "Required options:"
    echo ""
    echo "-r    (Password length range Ex. 8-15)"
    echo "-s    (Initial string to generate combinations)"
    echo "-p    (Position of the initial string [start/end])"
    echo "-o    (Output filename)"
    echo ""
    echo "Example: makeDict.sh -r 8-11 -s Testing -p end"
    echo ""
    echo "Output:"
    echo "XTesting"
    echo "XXTesting"
    echo "XXXTesting"
    echo "XXXXTesting"
    exit 1
fi

echo "Bien"
