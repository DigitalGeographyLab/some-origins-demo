"""

spatial_arcpy spatial join
Join attributes from world regions layer to point layer from nearest polygon.

"""

import os
import arcpy
import glob

# a bit lengthy way of ensuring corrent folder..(two levels up )
root_folder = os.path.dirname(os.path.dirname(os.getcwd()))

arcpy.env.overwriteOutput = True
arcpy.env.workspace = os.path.join(root_folder, r"demo_data\temp.gdb")


# folders

# On the first round, input is centroids based on all data,
# 2nd round centroids inside top regions,
# 3rd round centroids based on sub-regions
#source_folder = os.path.join(root_folder, r"demo_results\spatial_temp")
#source_folder = os.path.join(root_folder, r"demo_results\spatial_temp\hierarchical_reg")
source_folder = os.path.join(root_folder, r"demo_results\spatial_temp\hierarchical_subreg")

#-------------
# input files
#-------------

#Point layers
# Centroids identified inside continents:
print("Listing files..")
#files = glob.glob(os.path.join(source_folder,"*topRegCode_WGS84.shp"))
files = glob.glob(os.path.join(source_folder,"*_WGS84.shp"))

#World Regions (note, this folder is ignored in this repository due to it's size. Should be downloaded separately.
worldRegions = os.path.join(root_folder, r"world/Globl_regions_WGS84_7a_projOK.shp")
arcpy.AddSpatialIndex_management(worldRegions)

#---------------
# Spatial Join
#---------------

for pointFile in files:
    print("processing:" + os.path.basename(pointFile))
                  
    # Add spatial index
    print("spatial index..")
    arcpy.AddSpatialIndex_management(pointFile)

    outFile = os.path.join(source_folder, pointFile[:-4]+"_Regioninfo.shp")
    print("\nSpatial join...")
    arcpy.SpatialJoin_analysis(target_features=pointFile, join_features=worldRegions,
                               out_feature_class=outFile, match_option="CLOSEST_GEODESIC")

    print("Spatial join OK!...", outFile)
    
    

