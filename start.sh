#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
lxterminal -t "UDOO <--> VIPER Bridge" --working-directory="$DIR" -e bash -c "$DIR/udooviper.py"
