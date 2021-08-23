# bpm_pos_calc

## Overview
The goal of this project was to create something that aims to work on top of the Essentia package's beat detection system.
The original beat dectection often struggles on fade ins and fade outs, so the goal of this was to circumvent those issues.
In addition to fade ins and fade outs, this project also attempts to dectect multi-bpm songs. How this algorithm works is that
the Essentia algorithm first scans for what it thinks is
the location of the beats. From there, a certain percentage of the notes are
removed from the start and finish of the song. The reason for this is because we noticed
that the algorithm would often mess up on fade ins and fade outs. From there, we check to
see if the song is possibly a multi-bpm song by checking to see if a certain percentage of
the beats are within a similar range. If not, the program would consider that song multi-bpm. From the remaining beat locations, we calculate for
the average bpm. We then create a list of beat locations based on that bpm, where each beat
in that list is evenly spaced based on the bpm. From there, we would run an r squared calculation
comparing the new list of beats to the old list. That process will be repeated 100 times, with
each time having a slight offset. The offset with the lowest r squared value is then taken as
the new official list of beat positions. The notes cut off in the beginning are then placed back
according to the new list of beat positions. The program then writes those beat locations onto
the mp3 of the song.

## Prerequisites 
1. A linux machine
2. Python 3

## Install
    pip3 install essentia

## Usage
The program takes two arguments: the first argument being the song you would like to scan, and the second argument being the mp3 file in which to write the beeps onto. The second argument should be a copy of the first mp3.
For example:

    python3 beat_positions_calc.py example_song.mp3 output_example_song.mp3
   
Where example_song.mp3 is the song you would like to run through the program and output_example_song.mp3 is a copy of the same song.
