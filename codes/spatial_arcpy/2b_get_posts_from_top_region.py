"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

NOTE! This is not an arcpy code. ;)

This srcipt reads in the centroids, and gets users posts from that region /subregion for the hierarchical approach.

input:
    - Folder containing the centroids with region info (output of script 2b).

Next:
    - run the hierarchical homelocation script (1b). Repeat for regions and subregions. columns ["RegCode", "SubReg_2"]

"""


import geopandas as gpd
import pandas as pd
import glob
import os


#-----------------------
# SET INPUTS AND OUTPUTS
# ----------------------

# Full posting history
# input demo_data is in WGS84
some_fp = r"./demo_data/fake_input_data.shp"

#read file to GDB
some = gpd.read_file(some_fp)

# EXCLUDE POSTS WITHIN KRUGER NATIONAL PARK (ASSUME NO ONE LIVES THERE..even though in fact people do live there..)
some = some[some["FromKruger"] == 0]

#folder = r"./demo_results/spatial_temp"
folder = r"./demo_results/spatial_temp/hierarchical_reg"
#folder = r"C:\LocalData\VUOKKHEI\documents\some-origins\arcpy\hierarchical_subreg"
out_folder = r"./demo_results/spatial_temp/hierarchical_subreg"

# These files contain one centroid per user with regioninfo
files = glob.glob(os.path.join(folder, "*WGS84_Regioninfo.shp"))

# SET REGION LEVEL HERE!
# RegCode: continental regions, SubReg_2: sub-continental regions, FIPS: admin unit code (most often, a country)
hierarchyregion = "SubReg_2""RegCode"#"FIPS" # ##  #

#---------------------------------------------
# Get posting history from the detected region
# ---------------------------------------------

for input_file in files:
    data = gpd.read_file(input_file)
    method = os.path.basename(input_file).split("_")[0]
    print("processing ", method)

    # Select only userid and info of the region where the detected centroid was located:
    data = data[["userid", hierarchyregion]]

    #Inner join between full demo_data and top continent per each user
    joined = pd.merge(some, data, how="inner", on=["userid", hierarchyregion])
    print("Joined: ", method, len(joined), "records")

    # Points to file (these will be used as input in the next iteration of the hierarchical approach in script 1b)
    outfilename = os.path.join(out_folder, method + "_top" + hierarchyregion + "_posts.shp")
    joined.to_file(outfilename)


