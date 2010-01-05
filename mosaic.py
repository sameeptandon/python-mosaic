"""
mosaic.py
A simple python script that creates a mosaic from an input image. 

Dependencies:
Python Imaging Library, available at http://www.pythonware.com/products/pil/

Summary of methods:
print_fn(s) prints s to the terminal only when the verbose option is selected
gcd(a,b) returns the greatest common divisor of a and b
max_color(img) returns the most frequent color of img
average_value(img) returns the average R,G,B values of an img
square_crop(img) crops img into the largest possible square; the crop is centered
center_crop(img, resolution) crops img into the largest possible rectangle with aspect ratio resolution; the crop is centered
build_chest(directory) returns a computed dictionary with key=feature of img and val = directory location of img
nearest_neighbor(img, directory) finds the image in directory most similar to img based on feature
vector_error(v,u) returns the linear difference (sum) of two vectors u and v
mosaic(input_image, image_stash, resolution, thumbnail_size, func, num_of_images) does the magic
cleanup(input_image, directory) cleans up after the magic

Copyright (c) 2010, Sameep Tandon
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the Sameep Tandon nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Sameep Tandon BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

I feel legit using a Berkeley Software License. GO BEARS!

"""
import Image
import math
import os
import sys

inf = 1e1000
verbose = False

def print_fn( s ):
	
	"""
	prints diagnostic messages if the verbose option has been enabled
	@s: string s to print
	"""
	
	global verbose
	if verbose:
		print s

def gcd(a,b):
	
	"""
	Returns the greatest common divisor of two numbers, a and b
	@a: input number 1
	@b: input number 2
	"""
	
	while b != 0:
		a, b = b, a%b
	return a

def max_color (img): 
	
	"""
	Returns the most frequent color used in the img
	@img: An image object
	"""
	
	return max(	img.getcolors(img.size[0] * img.size[1]) )[1]


def average_value (img, lowerbound=(0,0), upperbound=None):

	"""
	Returns the average (R,G,B) of the image 
	@img: an Image object  
	@lowerbound: optional parameter; (min_x, min_y) tuple of pixels 
	@upperbound: optional parameter; (max_x, max_y) tuple of pixels 
	"""
	
	min_x, min_y = lowerbound
	if upperbound == None:
		upperbound = img.size
	max_x, max_y = upperbound
	img_width, img_height = img.size
	
	if min_x < 0 or min_y < 0 or max_x > img_width or max_y > img_height or max_x < min_x or max_y < min_y:
		print_fn ("Warning: Bad input; dumping data below.")
		print_fn ("img_width, img_height = " + str(img.size))
		print_fn ("min_x, min_y = " + str(lowerbound))
		print_fn ("max_x, max_y = " + str(upperbound))
		sys.exit(2)
		return None
	
	r = 0
	g = 0
	b = 0
	count = 0
	pix = img.load()

	for x in range(min_x, max_x):
		for y in range(min_y, max_y):
			temp_r, temp_g, temp_b = pix[x,y]
			r += temp_r
			g += temp_g
			b += temp_b
			count += 1
	
	return ( float(r) / float(count), float(g) / float(count), float(b) / float(count) )

def square_crop (img):
	"""
	Returns a square crop (with square at center) of an image
	@img: the input img file
	"""
	return center_crop(img, (1,1))

def center_crop (img, resolution, constrained_aspect_ratio=1):
	
	"""
	Returns an image file that has been cropped to be proportional to the resolution such that the crop is done in
	the center
	@img: the input img file
	@resolution: a tuple (x,y) for which the resulting image will be proportional to
	@constrained_aspect_ratio: an indicator stating whether the aspect ratio OF THE RESOLUTION must be constrained
	"""
		
	try:
		im = Image.open(img)
	except IOError:
		print_fn ("Could not open input image file at " + img)
		raise IOError 
	x,y = ( resolution[0] / gcd(resolution[0], resolution[1]), resolution[1] / gcd(resolution[0],resolution[1]) )
	im_width, im_height = im.size 
	
	box_x = 0
	box_y = 0
	if constrained_aspect_ratio: 
		while box_x+x <= im_width and box_y+y <= im_height:
			box_x += x
			box_y += y
		width_to_crop = im_width - box_x
		height_to_crop = im_height - box_y
	else:
		width_to_crop = im_width % resolution[0]
		height_to_crop = im_height % resolution[1]

	im = im.crop( (width_to_crop / 2 + (width_to_crop % 2), height_to_crop / 2 + (height_to_crop % 2), im_width - width_to_crop / 2, im_height - height_to_crop / 2) )
	return im 

def build_chest(directory, func=max_color, thumbnail_size=(50,50), num_of_images=None):
	"""
	Returns a dictionary with key = func(img), value = img
	@directory: a directory of images to build the mosaic out of
	@func: optional parameter; classification method used. average_value or max_color are viable choices
	@thumbnail_size: size of each image in the mosaic
	@num_of_images: max number of images to use 
	"""
	
	targetDir = os.getcwd() + "/" + directory + "/"
	tmpDir = targetDir + "temp/"
	
	if not os.path.isdir(tmpDir):
		os.mkdir(tmpDir)
		
	chest = { }
	
	if num_of_images == None:
		num_of_images = len(os.listdir(targetDir))
	
	
	for file in os.listdir(targetDir):
		if num_of_images > 0:
			try:
				im_transform = center_crop(targetDir + file, thumbnail_size)
				im_transform.thumbnail(thumbnail_size, Image.ANTIALIAS)
				print_fn ("Creating file " + tmpDir + os.path.splitext(file)[0] + ".thumbnail.jpg")
				im_transform.save(tmpDir + os.path.splitext(file)[0] + ".thumbnail.jpg", "JPEG")
				im_transform = Image.open(tmpDir + os.path.splitext(file)[0] + ".thumbnail.jpg")
				key = func(im_transform)
				chest[key] = tmpDir + os.path.splitext(file)[0] + ".thumbnail.jpg"
				num_of_images -= 1
			except IOError:
				print_fn (file + " is not an image file; Skipping it")
			
	return chest
		
def nearest_neighbor(img, chest, func=max_color, chest_keys=None): 

	"""
	Returns an image in the chest that is closest in color to img
	@img: img to classify
	@chest: a dictionary with key = func(img), value = img
	@func: optional parameter; classification method used. average_value or max_color are viable choices
	@chest_keys: optional parameter; all the keys of chest, used to save computation time
	"""
	
	if chest_keys == None:
		chest_keys = chest.keys()
	min_error = inf
	argmin_error = None
	img_val = func(img)
	for key in chest_keys:
		if vector_error(img_val, key) < min_error:
			min_error = vector_error(img_val, key)
			argmin_error = chest[key]
	return argmin_error
	
def vector_error (v, u):
	
	"""
	Returns the magnitude of the difference vector
	@v: vector v, represented as an iterable object in order (tuple or list)
	@u: vector u, same length as v
	"""

	diff = list(v)
	error = 0

	for i in range(0,len(v)):
		diff[i] -= u[i]
		error += math.fabs(diff[i])
		
	return error
	
def mosaic (input_image, image_stash, resolution=(25,25), thumbnail_size=(50,50), func=average_value, num_of_images=None):
	
	"""
	Saves an image file that is a mosaic of input_image. 
	@input_image: the location of the input image
	@image_stash: the directory of all the possible images to put in the mosaic 
	@resolution: a tuple (x,y) of size rectangles to break the input image into
	@thumbnail_size: the size of each thumbnail image in the mosaic
	@func: the classifier function to use
	@num_of_images: the number of images to use in the mosaic
	"""
	
	im = center_crop (input_image, resolution, False)
	chest = build_chest(image_stash, func, thumbnail_size, num_of_images)
	chest_keys = chest.keys( )
	im_width, im_height = im.size
	im.save(os.getcwd() + "/" + os.path.splitext(input_image)[0] + ".tmp.jpg", "JPEG")
	im = Image.open(os.getcwd() + "/" + os.path.splitext(input_image)[0] + ".tmp.jpg")
	mos_size = ((im_width / resolution[0]) * thumbnail_size[0], (im_height / resolution[1]) * thumbnail_size[1])
	mos = Image.new(im.mode, mos_size, (30, 20, 255))
	for x in range( im_width / resolution[0] ):
		print_fn (str(x+1) + " of " + str( im_width / resolution[0] ) + " columns")
		for y in range (im_height / resolution[1] ):
			start_x = x * resolution[0]
			start_y = y * resolution[1]
			end_x = start_x + resolution[0]
			end_y = start_y + resolution[1]
			box = (start_x, start_y, end_x, end_y)
			query = im.transform(resolution, Image.EXTENT,box)
			reply = Image.open( nearest_neighbor(query, chest, func, chest_keys) )
			start_x = x * thumbnail_size[0]
			start_y = y * thumbnail_size[1]
			end_x = start_x + thumbnail_size[0]
			end_y = start_y + thumbnail_size[1]
			box = (start_x, start_y, end_x, end_y)
			mos.paste(reply, box)
	mos.save(os.getcwd() + "/" + os.path.splitext(input_image)[0] + ".mosaic.jpg", "JPEG")
	cleanup( input_image, image_stash )
	
def cleanup(input_image, directory):
	"""
	Cleans up the mess
	@input_image: filename of the input image
	@directory: the directory where the mess was made
	"""
	print_fn ("Initializing cleanup procedure. Deleting tmp files") 
	targetDir = os.getcwd() + "/" + directory + "/"
	tmpDir = targetDir + "temp/"
	os.remove(os.getcwd() + "/" + os.path.splitext(input_image)[0] + ".tmp.jpg")
	 
	for file in os.listdir(tmpDir):
		print_fn ("Removing file " + tmpDir + file)
		os.remove(tmpDir + file)
	os.removedirs(tmpDir)
	print_fn ("Cleanup complete.") 

def main(): 
	from optparse import OptionParser
	usage = "usage: %prog -i [input image] -s [directory of images] -r [x] [y] -t [x] [y]\n"
	usage += "Optional arguments -n, -a, -v"
	parser = OptionParser(usage=usage)
	parser.add_option("-i", "--input", dest="input_image", help="Input Image File")
	parser.add_option("-s", "--stash", dest="image_stash", help="Directory of images")
	parser.add_option("-r", "--resolution", dest="resolution", help="Size of tile to inspect at in input image", nargs=2)
	parser.add_option("-t", "--thumbnail", dest="thumbnail", help="Size of tile to write in output image", nargs=2)
	parser.add_option("-n", "--numImages", dest="number_of_images", help="Number of images to look at in stash")
	parser.add_option("-a", "--averageValue", dest="func", help="Average Value Classifier; instead of default MAX_COLOR. Average Value is better, but slower", action="store_true")
	parser.add_option("-v", "--verbose", dest="verbose", help="Verbose option; Prints diagnostic messages", action="store_true")
	(options, args) = parser.parse_args()
	if not options.input_image or not options.image_stash or not options.resolution or not options.thumbnail or not len(options.resolution)==2 or not len(options.thumbnail) == 2:
		print "Incorrect Usage; please see python mosaic.py --help"
		sys.exit(2)
	if options.verbose:
		global verbose
		verbose = True
	try:
		input_image = options.input_image
		image_stash = options.image_stash
		resolution = ( int(options.resolution[0]), int(options.resolution[1]) )
		thumbnail_size = ( int(options.thumbnail[0]), int(options.thumbnail[1]) )
		func = max_color
		if options.func:
			func = average_value
	except:
		print "Incorrect Usage; please see python mosaic.py --help"
		sys.exit(2)
	if options.number_of_images:
		number_of_images = int(options.number_of_images)
		mosaic( input_image, image_stash, resolution, thumbnail_size, func, number_of_images )
	else:
		mosaic( input_image, image_stash, resolution, thumbnail_size, func)
	sys.exit()

if __name__ == "__main__":
		main()

	