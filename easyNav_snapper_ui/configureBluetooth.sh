#!/bin/bash

hciconfig hci0 reset
sdptool add --channel=22 SP
rfcomm listen /dev/rfcomm0 22