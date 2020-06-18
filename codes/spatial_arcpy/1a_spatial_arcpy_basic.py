"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - SPATIAL - BASIC

Dependencies:
    arcpy

Tested to work in Python 2.7 that comes with ArcMap 10.3

Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA.
The script calculates following things:
    -Based on each user's posts, calculate the
        - Standard deviational ellipse --> center point of ellipse
        - Standard distance circle --> center point of circle
        - Mean center
        - Media center

Outputs:
    - 2 x intermediate polygon layers(SD Ellipses & SD Circles) 
    - 4 x point layers in WGS84 (one for each method)

Next steps for the basic approach:
    - 2a_join_region_info_to_centroids.py (joins region info to centroids)
    - 3_shp_to_csv.py (prepare result file with detected origin countries)

Next steps for the hierarchical approach:
    - 2a_join_region_info_to_centroids.py (joins region info to centroids; adjust region code)
    - 2b_get_posts_from_top_region.py (get posts from each users top region)
    - 1b_spatial_arcpy_hierarchical.py (re-run the centrographic methods on the demo_data subsets)

"""
import arcpy
import os

#Enable output overwriting
arcpy.env.overwriteOutput = True

# a bit lengthy way of ensuring corrent folder..(two levels up )
root_folder = os.path.dirname(os.path.dirname(os.getcwd()))

arcpy.env.workspace = os.path.join(root_folder, r"demo_data\temp.gdb")


def MapCentroids(inputFile, outputFile):
    """Creates a new layer based on X Y demo_data in shapefile's attribute table"""
    inputdbf = inputFile[:-4] + ".dbf"

    out_temp = "centroids"

    print("Plotting centroinds to map...")
    arcpy.MakeXYEventLayer_management(inputdbf,"CenterX", "CenterY", out_temp, spatial_reference=arcpy.SpatialReference(54032))

    # Save to file...
    arcpy.CopyFeatures_management(out_temp, outputFile)

    # Project layer to 'WGS84'
    outputwgs84 = outputFile[:-4] + "_WGS84.shp"
    print("Projecting layer to WGS84...")
    arcpy.Project_management(outputFile, outputwgs84, arcpy.SpatialReference(4326))    
    
#------------------------------
# Inputs & outputs
#------------------------------

#output folder
out_folder = os.path.join(root_folder, r"demo_results\spatial_temp")

# input demo_data is in WGS84
points = os.path.join(root_folder, r"demo_data\fake_input_data.shp")

# output file for projected input layer
points_projected = os.path.join(out_folder, "somemobility_projected.shp")

# output files
SD_Ellipses = os.path.join(out_folder, "SDEllipses.shp")
Ellipse_centroids = os.path.join(out_folder, "EllipseCentroids.shp")

SD_Circles = os.path.join(out_folder, "SDCircles.shp")
Circle_Centroids = os.path.join(out_folder, "CircleCentroids.shp")

Mean_Center = os.path.join(out_folder, "MeanCenters.shp")
Median_Center = os.path.join(out_folder, "MedianCenters.shp")

#---------------------
# Project input demo_data
#---------------------

# Create projected layer if it does not exist
if os.path.isfile(points_projected) == False: 

    print("Projecting input demo_data...")
    
    # Project layer to Azimuthal equidistant projection:
    # https://desktop.arcgis.com/en/arcmap/10.3/guide-books/map-projections/azimuthal-equidistant.htm
    arcpy.Project_management(points, points_projected, arcpy.SpatialReference(54032))

    print("projection ok!\n")
    
else:
    print("using existing projected point file\n")

#----------------
# SD Ellipse
#----------------
print("Creating Ellipses...")
# This tool Creates standard deviational ellipses to summarize the spatial characteristics of geographic features:
# central tendency, dispersion, and directional trends.
# http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/directional-distribution.htm
# Create SD Ellipses for each user
# Syntax: DirectionalDistribution_stats (Input_Feature_Class, Output_Ellipse_Feature_Class, Ellipse_Size, {Weight_Field}, {Case_Field})
if os.path.isfile(SD_Ellipses) == False:
    arcpy.DirectionalDistribution_stats(points_projected, SD_Ellipses, "1_STANDARD_DEVIATION", "#", Case_Field="userid")
else:
    print("using existing file")

# Plot centroids to map and project to WGS84
MapCentroids(SD_Ellipses, Ellipse_centroids)

print("Ellipses ok!\n")

#-------------------
# Standard Distance
#-------------------
print("Creating Standard Distance Circles...")

# This tool Measures the degree to which features are concentrated or dispersed around the geometric mean center
# http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/standard-distance.htm
# Syntax: StandardDistance_stats (Input_Feature_Class, Output_Standard_Distance_Feature_Class, Circle_Size, {Weight_Field}, {Case_Field})

if os.path.isfile(SD_Circles) == False:
    arcpy.StandardDistance_stats(points_projected, SD_Circles, "1_STANDARD_DEVIATION", "#", Case_Field="userid")

else:
    print("using existing file")
    
# Plot centroids to map and project to WGS84
MapCentroids(SD_Circles, Circle_Centroids)

print("Circles ok!\n")

#-----------------
# Mean Center
#-----------------
print("Calculating Mean Center...")

# This tool Identifies the geographic center (or the center of concentration) for a set of features
# http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/mean-center.htm
# Syntax: MeanCenter_stats (Input_Feature_Class, Output_Feature_Class, {Weight_Field}, {Case_Field}, {Dimension_Field})
if os.path.isfile(Mean_Center) == False:
    arcpy.MeanCenter_stats(points_projected, Mean_Center, Case_Field="userid")
else:
    print("using existing file")


#Projecting the mean centers to WGS84
arcpy.Project_management(Mean_Center, Mean_Center[:-4] + "_WGS84.shp", arcpy.SpatialReference(4326))
print("Mean Center ok!\n")

#-----------------
# Median Center
#-----------------
print("Calculating Median Center...")

# This tool Identifies the location that minimizes overall Euclidean distance to the features in a dataset
# https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/median-center.htm
# Syntax: MedianCenter_stats (Input_Feature_Class, Output_Feature_Class, {Weight_Field}, {Case_Field}, {Attribute_Field})
if os.path.isfile(Median_Center) == False:
    arcpy.MedianCenter_stats(points_projected,  "median_centers_temp", Case_Field="userid")
else:
    print("using existing file")


#Projecting the median centers to WGS84
arcpy.Project_management("median_centers_temp", Median_Center[:-4] + "_WGS84.shp", arcpy.SpatialReference(4326))

print("Median Center ok!\n")

# DONE
print("DONE! Restults in folder: ", out_folder)

