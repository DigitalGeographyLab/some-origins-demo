"""
Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - SPATIAL - HIERARCHICAL

Inputs:
    - Folder containing social media posts FROM THE REGION where the detected origin was located
    - inputs have been generated using
        1a_spatial_arcpy_basic.py,
        2a_join_region_info_to_centroids.py and
        2b_get_posts_from_top_region.py

Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA.
The script calculates following things:
    - Project input layer to World_Mollweide -projection
    -For posts of each user, calculate the
        - Standard deviational ellipse --> center point of ellipse
        - Standard distance circle --> center point of circle
        - Mean center
        - Median center

Outputs:
    - projected input file
    - 2 x intermediate polygon layers (SD Ellipses & SD Circles) 
    - 4 x point layers in WGS84

Next steps:
    - 2a_join_region_info_to_centroids.py and
    - 2b_get_posts_from_top_region.py
    - [Repeat scrits 1b, 2a, 2b for sub-regions.]
    - 3_shp_to_csv.py

"""
import arcpy
import os
import glob

# a bit lengthy way of ensuring corrent folder..(two levels up )
root_folder = os.path.dirname(os.path.dirname(os.getcwd()))

arcpy.env.overwriteOutput = True
arcpy.env.workspace = os.path.join(root_folder, r"demo_data\temp.gdb")

def MapCentroids(inputFile, outputFile):
    """Creates a new layer based on X Y datain shapefile's attribute table"""
    
    inputdbf = inputFile[:-4] + ".dbf"

    out_temp = "centroids"

    print("Plotting centroinds to map...")
    arcpy.MakeXYEventLayer_management(inputdbf, "CenterX", "CenterY", out_temp, spatial_reference=arcpy.SpatialReference(54032))

    # Save to file...
    arcpy.CopyFeatures_management(out_temp, outputFile)

    # Project layer to 'WGS84'
    outputwgs84 = outputFile[:-4] + "_WGS84.shp"
    print("Projecting layer to WGS84...")
    arcpy.Project_management(outputFile, outputwgs84, arcpy.SpatialReference(4326))

#------------------------------
# Inputs & outputs
#------------------------------

# Read in subset of posts in the target region
#files = glob.glob(os.path.join(root_folder, r"demo_results/spatial_temp/hierarchical_reg/*topRegCode_posts.shp"))
files = glob.glob(os.path.join(root_folder, r"demo_results/spatial_temp/hierarchical_subreg/*topSubReg_2_posts.shp"))


#Result folder
#result_folder = os.path.join(root_folder, r"demo_results/spatial_temp/hierarchical_reg")
result_folder = os.path.join(root_folder, r"demo_results/spatial_temp/hierarchical_subreg")


#---------------------
# Project input demo_data
#---------------------

for pointFile in files:

    method = os.path.basename(pointFile).split("_")[0]
    region = os.path.basename(pointFile).split("_")[1]
    outfile = os.path.join(result_folder, method + "_" + region + ".shp")
    print("Filename is set:", outfile)

    points_projected = pointFile[:-4] + "_projected.shp"

    # Create projected layer if it does not exist
    if os.path.isfile(points_projected) == False:

        print(os.path.basename(points_projected) + " did not exists, re-projecting..")

        print("Projecting input demo_data...")
        
        # Project layer to Azimuthal equidistant projection:
        # https://desktop.arcgis.com/en/arcmap/10.3/guide-books/map-projections/azimuthal-equidistant.htm
        arcpy.Project_management(pointFile, points_projected, arcpy.SpatialReference(54032))

        print("projection ok!\n")
        
    else:
        print("using existing projected point file\n")

    #----------------
    # SD Ellipse
    #----------------
    
    #This tool Creates standard deviational ellipses to summarize the spatial characteristics of geographic features: central tendency, dispersion, and directional trends.
    # http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/directional-distribution.htm
    # Create SD Ellipses for each user
    # Syntax: DirectionalDistribution_stats (Input_Feature_Class, Output_Ellipse_Feature_Class, Ellipse_Size, {Weight_Field}, {Case_Field})
    if method == "EllipseCentroids":
        print("Creating Ellipses...")
        ellipse_file = os.path.join(result_folder, "Ellipses.shp")
        arcpy.DirectionalDistribution_stats(points_projected, ellipse_file, "1_STANDARD_DEVIATION", "#", Case_Field="userid")

        # Plot centroids to map and project to WGS84
        MapCentroids(ellipse_file, outfile[:-4] + ".shp")

        print("Ellipses ok!\n")
    else:
        print("...")

    #-------------------
    # Standard Distance
    #-------------------
    
    # This tool Measures the degree to which features are concentrated or dispersed around the geometric mean center
    # http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/standard-distance.htm
    # Syntax: StandardDistance_stats (Input_Feature_Class, Output_Standard_Distance_Feature_Class, Circle_Size, {Weight_Field}, {Case_Field})

    if method == "CircleCentroids":
        print("Creating Standard Distance Circles...")
        circle_file = os.path.join(result_folder, "Circles.shp")
        arcpy.StandardDistance_stats(points_projected, circle_file, "1_STANDARD_DEVIATION", "#", Case_Field="userid")

        # Plot centroids to map and project to WGS84
        MapCentroids(circle_file, outfile[:-4] + ".shp")
        
        print("Circles ok!\n")
    else:
        print("...")
        
    #-----------------
    # Mean Center
    #-----------------
    
    # This tool Identifies the geographic center (or the center of concentration) for a set of features
    # http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/mean-center.htm
    # Syntax: MeanCenter_stats (Input_Feature_Class, Output_Feature_Class, {Weight_Field}, {Case_Field}, {Dimension_Field})
    if method == "MeanCenters":
        print("Calculating Mean Center...")
        arcpy.MeanCenter_stats(points_projected, "mean_center_temp", Case_Field="userid")

        #Projecting the mean centers to WGS84
        arcpy.Project_management("mean_center_temp", outfile[:-4] + "_WGS84.shp", arcpy.SpatialReference(4326))
        print("Mean Center ok!\n")
    else:
        print("...")


    #-----------------
    # Median Center
    #-----------------

    # This tool Identifies the location that minimizes overall Euclidean distance to the features in a dataset
    # https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/median-center.htm
    # Syntax: MedianCenter_stats (Input_Feature_Class, Output_Feature_Class, {Weight_Field}, {Case_Field}, {Attribute_Field})
    if method == "MedianCenters":
        print("Calculating Median Center...")
        arcpy.MedianCenter_stats(points_projected,  "median_centers_temp", Case_Field="userid")

        #Projecting the median centers to WGS84
        arcpy.Project_management("median_centers_temp", outfile[:-4] + "_WGS84.shp", arcpy.SpatialReference(4326))

        print("Median Center ok!\n")

    # DONE

    print("DONE!", method, "Restults in folder: ", result_folder)


