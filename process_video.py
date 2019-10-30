from __future__ import division
import subprocess as sp
import numpy
from PIL import Image, ImageDraw
import re
import time
import sys
import math

# Open the video file. In Windows you might need to use FFMPEG_BIN="ffmpeg.exe"; FFMPEG_BIN = "ffmpeg" # on Linux ans Mac OS
FFMPEG_BIN = "ffmpeg" #if ffmpeg was manually installed, need to include path

# Timestamp so you can see how long it took
start_time = "Script started at " + time.strftime("%H:%M:%S")
print start_time

# optional starting time hh:mm:ss.ff; default value set to 00:00:00.0
hh = "%02d" % (0,)
mm = ":%02d" % (0,)
ss = ":%02d" % (0,)
ff = ".0"
print "Timestamp for first frame: "+hh+mm+ss+ff

# input file (first argument)
filename = str(sys.argv[1])

#parsing out dimensions from video file
command = ['ffprobe', '-v', 'error',
           '-select_streams', 'v:0',
           '-show_entries', 'stream=width,height',
           '-of', 'default=nw=1:nk=1', filename]
dimension = sp.check_output(command)
dimension = [int(i) for i in dimension.splitlines()]
width = dimension[0]
height = dimension[1]

#parsing out framerate from video file
command = ['ffprobe', '-v', 'error', 
           '-select_streams', 'v', '-of', 
           'default=noprint_wrappers=1:nokey=1', 
           '-show_entries', 'stream=r_frame_rate', filename]
fr = sp.check_output(command)
fr = [int(i) for i in fr. split('/')]
fr = fr[0]/fr[1]

# parsing out runtime from video file
command = ['ffprobe', '-v', 'error', 
           '-show_entries', 'format=duration', 
           '-of', 'default=noprint_wrappers=1:nokey=1', filename]
runtime = sp.check_output(command)
runtime = float(runtime)

nthFrame = math.floor(fr * runtime / 4096) #(fps * total runtime(s)) / 4096
if nthFrame < 1: # if the runtime is too short, the frame sampling will be set at 1
    nthFrame = 1
    
# output image file (same as input file, with non-alphanums stripped):
outfilename = re.sub(r'\W+', '', filename) + ".png"
print "Filename:", filename
print "Dimensions:", width, height

###
### This section: credit to http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/

command = [ FFMPEG_BIN,
            '-threads', '4',
            '-ss', hh+mm+ss,
            '-i', filename,
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo', '-']
pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)

# get the average rgb value of a frame
def draw_next_frame_rgb_avg(raw_frame):    
    frame =  numpy.fromstring(raw_frame, dtype='uint8')
    frame = frame.reshape((height,width,3))    
    rgb_avg = int(numpy.average(frame[:,:,0])),int(numpy.average(frame[:,:,1])),int(numpy.average(frame[:,:,2]))
    return rgb_avg


# Go through the pipe one frame at a time until it's empty; store each frame's RGB values in rgb_list 
rgb_list = []
x = 1 # optional; purely for displaying how many frames were processed
while pipe.stdout.read(width*height*3): # as long as there's data in the pipe, keep reading frames
    x = x + 1
    if x % nthFrame == 0:
        try:
            rgb_list.append(draw_next_frame_rgb_avg(pipe.stdout.read(width*height*3)))
        except:
            print "No more frames to process (or error occurred). Number of frames processed:", x

# create a new image width the same width as number of frames sampled,
# and draw one vertical line per frame at x=frame number
image_height = 2160 # set image height to whatever you want; you could use int(len(rgb_list)*9/16) to make a 16:9 image for instance
new = Image.new('RGB',(len(rgb_list),image_height))
draw = ImageDraw.Draw(new)
# x = the location on the x axis of the next line to draw
x_pixel = 1
for rgb_tuple in rgb_list:
    draw.line((x_pixel,0,x_pixel,image_height), fill=rgb_tuple)
    x_pixel = x_pixel + 1
new.show() 
new.save(outfilename, "PNG")

print start_time
print "Script finished at " + time.strftime("%H:%M:%S")
print "Frames" + str(len(rgb_list))