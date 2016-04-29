import fiona
import shapely
import numpy as np
import xray
import sys
import argparse

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

import gridfunctions

shpfile = fiona.open(sys.argv[1])
feature_count = len(shpfile)
print("{} features found".format(feature_count))

ncfile = xray.open_dataset(sys.argv[2])
print ncfile.data_vars
print ncfile.coords

try:
	lats = ncfile['lat']
	lons = ncfile['lon']
except:
	lats = ncfile['latitude']
	lons = ncfile['longitude']

longrid, latgrid = np.meshgrid(lons, lats)

# Get grid and shapes
shape, grid_polys = gridfunctions.makegrid(lats, lons)
print("grid has shape {}".format(repr(shape)))

# We'll keep all the weights
weights = np.zeros((len(shpfile), shape[0], shape[1]), dtype=np.float32)

# Create the output shapefile based on the source shapefile
schema = shpfile.schema

for varname in ncfile.data_vars.keys():
	for ti in range(0, len(ncfile.coords['time'])):
		schema['properties']['{}_t{}'.format(varname, ti+1)] = 'float'

print schema
outshpfile = fiona.open(sys.argv[3], 'w', driver=shpfile.driver, crs=shpfile.crs, schema=schema)


feature_id = 0
patches = []
for feature in shpfile:

	print type(feature)
	print feature['properties']	
	shape = shapely.geometry.shape(feature['geometry'])
	
	try:
		patches.append(PolygonPatch(shape, fc='green', ec='#555555', lw=0.2, alpha=1., zorder=100))
	except:
		pass

	# Sweep the grid (this could be more efficient by pre-culling)
	x, y = 0, 0
	for row in grid_polys:		
		for poly in row:
			if poly.intersects(shape):
				weights[feature_id,y,x] = poly.intersection(shape).area / poly.area
				weights[feature_id] = weights[feature_id]/np.sum(weights[feature_id])
			x += 1
		
		x = 0
		y += 1

	# Calculate area weighted mean for each data variable
	for varname in ncfile.data_vars.keys():
		for ti in range(0, len(ncfile.coords['time'])):
			value = np.sum(ncfile[varname][ti] * weights[feature_id])
			feature['properties']['{}_t{}'.format(varname, ti+1)] = float(value)
		
		#print "writing"
		print feature['properties']
		#print outshpfile.schema
		outshpfile.write(feature)


outshpfile.close()



