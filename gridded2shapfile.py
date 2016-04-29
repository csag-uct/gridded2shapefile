import fiona
import shapely
import numpy as np
import xray
import sys
import argparse

import gridfunctions


# Read source/template shapefile
shpfile = fiona.open(sys.argv[1])
feature_count = len(shpfile)
print("{} features found".format(feature_count))

# Open source netcdf data file
ncfile = xray.open_dataset(sys.argv[2])
print ncfile.data_vars
print ncfile.coords

# Try and get the latitude/longitude variables
try:
	lats = ncfile['lat']
	lons = ncfile['lon']
except:
	lats = ncfile['latitude']
	lons = ncfile['longitude']

# Construct full 2D lat/lon grids
longrid, latgrid = np.meshgrid(lons, lats)

# Construct polygon grid
shape, grid_polys = gridfunctions.makegrid(lats, lons)
print("grid has shape {}".format(repr(shape)))

# We'll keep all the weights, we could write these out as well
weights = np.zeros((len(shpfile), shape[0], shape[1]), dtype=np.float32)

# Create the output shapefile based on the source shapefile schema

schema = shpfile.schema

for varname in ncfile.data_vars.keys():
	for ti in range(0, len(ncfile.coords['time'])):
		schema['properties']['{}_t{}'.format(varname, ti+1)] = 'float'

print schema
outshpfile = fiona.open(sys.argv[3], 'w', driver=shpfile.driver, crs=shpfile.crs, schema=schema)


# Okay here, we go, iterate through the template features
feature_id = 0
patches = []
for feature in shpfile:

	# Get the actual geometry
	shape = shapely.geometry.shape(feature['geometry'])
	
	# Sweep the grid (this could be much more efficient by pre-culling based on geometry bounding box)
	x, y = 0, 0
	for row in grid_polys:
		for poly in row:
			if poly.intersects(shape):
				weights[feature_id,y,x] = poly.intersection(shape).area / poly.area
				weights[feature_id] = weights[feature_id]/np.sum(weights[feature_id])  # Normalize to sum = 1
			x += 1
		
		x = 0
		y += 1

	# Calculate area weighted mean for each data variable
	for varname in ncfile.data_vars.keys():
		for ti in range(0, len(ncfile.coords['time'])):
			value = np.sum(ncfile[varname][ti] * weights[feature_id])
			feature['properties']['{}_t{}'.format(varname, ti+1)] = float(value)
		
		print feature['properties']
		outshpfile.write(feature)


outshpfile.close()



