#!/bin/bash
adb logcat -v threadtime | grep `adb shell ps | grep $1 | cut -c10-15`