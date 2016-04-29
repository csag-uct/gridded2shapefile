# gridded2shapefile
Code to convert gridded data (netCDF) to a shapefile

This code takes as arguments a template shapefile and a netcdf gridded data file (CF compliant).  For each feature in the
template shapefile a set of normalized weights on the netcdf spatial grid is produced that represent the fractional overlap of the 
feature geometry and each grid cell (grid coordinates are assumed to be grid centers so grid cells are constructed around the
grid centers.  The weights are normalized so sum to 1.

A new shapefile is written out that contains all the same features and properties as the template shapefile but also includes
a new property per variable and timestep in the source netcdf file.  The property names are constructed like this:

[variablename]_t[timestep+1]

So if you source netcdf file has two variables, tasmax and tasmin, for 12 months of the year, you'll end up with 24 new properties 
in the shapefile schema: tasmax_t1, taxmin_t1, tasmax_t2, tasmin_t2, ... tasmax_t12, tasmax_t12

The values of the properties are the sum of the product of the grid weights for the feature geometry and the gridded values for each timestep.
This produces an area weighted mean for each target geometry.

## Future development?
An option should be added construct timeseries statistics rather than a full time series so that property values could represent the 
time mean or such like derivatives.  At this point it more pragmatic to calculate these in gridded form (CDO or equivalent) and then
map into shapefile geometries using gridded2shapefile


