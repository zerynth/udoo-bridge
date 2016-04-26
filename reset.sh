#!/bin/bash
  echo "out" > /sys/class/gpio/gpio0/direction
  echo 0 > /sys/class/gpio/gpio0/value
  sleep 0.1
  echo 1 > /sys/class/gpio/gpio0/value
  echo "in" > /sys/class/gpio/gpio0/direction
