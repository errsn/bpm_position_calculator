#!/usr/bin/env python

# Copyright (C) 2006-2021  Music Technology Group - Universitat Pompeu Fabra
# Copyright (C) 2021, Erick Sun, erick@junsun.net
#
# This file is part of Essentia
#
# Essentia is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the Affero GNU General Public License
# version 3 along with this program. If not, see http://www.gnu.org/licenses/

#
# The original purpose of this algorithm was to try and make something that could assist in osu! mapping.  
# Although it didn't perfectly achieve this goal, it was an interesting project and I feel that it still has some limited applications.
# 
# How this algorithm works is that  the Essentia algorithm first scans for what it thinks is
# the location of the beats. From there, a certain percentage (cutoff_val) of the notes are
# removed from the start and finish of the song. The reason for this is because we noticed
# that the algorithm would often mess up on fade ins and fade outs. From there, we check to
# see if the song is possibly a multi-bpm song by checking to see if a certain percentage of
# the beats are within a similar range. From the remaining beat locations, we calculate for
# the average bpm. We then create a list of beat locations based on that bpm, where each beat
# in that list is evenly spaced based on the bpm. From there, we would run an r squared calculation
# comparing the new list of beats to the old list. That process will be repeated 100 times, with
# each time having a slight offset. The offset with the lowest r squared value is then taken as
# the new official list of beat positions. The notes cut off in the beginning are then placed back
# according to the new list of beat positions. The program then writes those beat locations onto
# the mp3 of the song.
#

from collections import Counter
import sys
import statistics 
import matplotlib.pyplot as plt
import numpy
from essentia.standard import *


time_dis_list = []
cutoff_val = 0.10
bucket_val = 0.05
average = 0
manual_bpm_status = 0
list_of_r = []
final_list = []
final = []


# This function creates the points that are compared to the original beat positions used in the r squared calcuation 
def ruler_creation(offset, index):
	return(beats[0] + offset + avg_dis*index, beats[0] + offset + avg_dis*(index-1))

# This function calculates r squared
def compute_r(offset):
	if offset < (beats[1] - beats[0])/2:
		sum = offset ** 2
	elif offset > (beats[1] - beats[0])/2:
		sum = (avg_dis - offset) ** 2
	x = 1
	while offset < beats[-1] + avg_dis:
		ruler, ruler_1 = ruler_creation(offset, x)
		if x > len(beats) - 1:
			return(sum/len(beats))
			exit()
		elif beats[x] <= ruler and beats[x] >= ruler_1:
			if abs(beats[x] - ruler) < abs(beats[x] - ruler_1):
				sum += (beats[x] - ruler) ** 2
			else:
				sum += (beats[x] - ruler_1) ** 2
		x += 1					

# This function creates a list of the intervals in seconds between all beats
def finding_time_dis():
	x = 0
	while x + 1 < len(beats):
		z = beats[x]
		y = beats[x+1]
		time_dis = y - z
		time_dis_list.append(round(time_dis,4))
		x = x + 1

# This function removes the X percent of beats in the front and the back of the song
def trimming_time_dis_list(num_to_rm):
	del time_dis_list[:num_to_rm]
	del time_dis_list[-num_to_rm:]
	del beats[:num_to_rm]
	del beats[-num_to_rm - 1:]

# This detects for potential very clear multi-bpm songs
def multi_bpm_filter():
	num_of_clean = 0
	val_of_clean = 0
	common = Counter(time_dis_list).most_common()
	tops = common[:3]
	for x in tops:
		x = list(x)
		val_of_clean += x[0] * x[1]
		num_of_clean += x[1]

	if len(time_dis_list) * .90 > num_of_clean:
		print("BPM Error. Less than 90% of notes are correct.")
		exit()

	x = 0
	while x <= 1:
		if list(tops[x])[0] * .9 > list(tops[x+1])[0] or list(tops[x])[0] * 1.1 < list(tops[x+1])[0]:
			print("BPM Error. Multiple significant spacing dectected.")
			exit()
		x += 1

	return val_of_clean, num_of_clean

# This function finds the lowest r squared value and creates the final official list of beat locations
def optimal_beat_spot_calc():
	x = 0

	m_0 = beats[0]

	while m_0 <= beats[1]:
		list_of_r.append(compute_r(m_0 - beats[0]))
		m_0 += avg_dis/100

	lowest_r = min(list_of_r)
	final_offset = (list_of_r.index(lowest_r)) * (avg_dis/100) - .03
	beat = beats[0]
	x = 0
	while beat <= final_beat - avg_dis:
		final_list.append(beat + final_offset)
		beat += avg_dis
		
	beat = beats[0]
	while beat + final_offset >= 0:
		final_list.append(beat + final_offset)
		beat -= avg_dis

	for i in final_list:
		if i not in final:
			final.append(i)

# This function asks the user if they would like to double the bpm, as the original Essentia algorithm often only counts every other beat. It then writes the new beats onto an
def double_bpm():
	if double.lower() == "no" or double.lower() == "n":
		print('Writing audio files to disk with beats marked...')
		final.sort()
		#for x in final:
			#print("26,84," + str(round(x*1000 - 30)) + ",5,4,0:0:0:0:")

		marker = AudioOnsetsMarker(onsets = final, type = 'beep')
		marked_audio = marker(audio)
		MonoWriter(filename = output_filename)(marked_audio)

		print("Would you like to see the time position of the beats?")
		ddd = input()
		if ddd.lower() == 'y' or ddd.lower() == 'yes':
			print(final)

		print('All done!')
		
	elif double.lower() == "yes" or double.lower() == "y":
		final_2 = final.copy()
		for x in final:
			final_2.append(x + 0.5 * avg_dis)

		final_2.sort()
		del final_2[-1]
		#for x in final_2:
			#print("26,84," + str(round(x*1000 - 30)) + ",5,4,0:0:0:0:")
		
		print("BPM of the song is : " + str(2*bpm))
		print('Writing audio files to disk with beats marked...')

		marker = AudioOnsetsMarker(onsets = final_2, type = 'beep')
		marked_audio = marker(audio)
		MonoWriter(filename = output_filename)(marked_audio)
		print("Would you like to see the time position of the beats? (Y/N)")
		ddd = input()
		if ddd.lower() == 'y' or ddd.lower() == 'yes':
			print(final_2)

		print('All done!')
	else:
		print("Error. Try again")
		exit() 

# This function asks if one would like to manually enter the bpm of the song
def manual_bpm():
	print("Enter bpm here:")
	mb = input()
	#print(60/float(mb))
	return float(mb)/2 , 120/float(mb)

# This function explains how to use the program
def usage():
	print("This function takes two arguments. The first argument is the mp3 of the song you would like to use. The second argument should be the same mp3 but a copy of it, as that is the mp3 the program will write the beat locations onto. On each beat location, the program will place a small beep sound")
	exit()

# In this example we are going to look at how to perform beat tracking
# and mark extractred beats on the audio using the AudioOnsetsMarker algorithm.

if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "-h"):
	usage()

# we're going to work with an input and output files specified as an argument in the command line
try:
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
except:
    print('usage: %s <input-audiofile> <output-audiofile>' % sys.argv[0])
    sys.exit()

# don't forget, we can actually instantiate and call an algorithm on the same line!
print('Loading audio file...')
audio = MonoLoader(filename = input_filename)()

# compute beat positions
print('Computing beat positions...')
bt = BeatTrackerMultiFeature()
beats, _ = bt(audio)
beats = beats.tolist()
final_beat = beats[-1]

finding_time_dis()

num_to_rm = round(len(time_dis_list) * cutoff_val)
trimming_time_dis_list(num_to_rm)

val_of_clean, num_of_clean = multi_bpm_filter()
bpm = round(60/(val_of_clean/num_of_clean),2)
avg_dis = val_of_clean/num_of_clean

print("Would you like to manually input the bpm of the song? (Y/N)")
yn = input()
if yn.lower() == 'y' or yn.lower() == 'yes':
	bpm, avg_dis = manual_bpm()
	manual_bpm_status = 1

print("Calculating optimal beat positions")
x = 0

optimal_beat_spot_calc()


if manual_bpm_status == 0:
	print("BPM of the song is : " + str(bpm))
	print("Would you like to double the bpm of the song? (Y/N)")
	double = input()
	double_bpm()

elif manual_bpm_status == 1:
	double = "y"
	double_bpm()

