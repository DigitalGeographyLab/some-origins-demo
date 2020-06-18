"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

Join cluster results together with expert assesment in order to select the most suitable epsilon value
This script produces information to the supplementary materials.

"""

import os
import glob
import pandas as pd
import geopandas as gpd

#------------------------------
# Read in cluster results
#------------------------------
method = "hierarchical" #'basic'
region_column = 'FIPS'  #'SubReg_2'# "RegCode"#

# Results by user
output_folder = r"./demo_results/cluster_options"

cluster_folder = r"./demo_results/cluster_options/hierarchical_%s" % region_column

#cluster_folder = r"P:\h510\some\manuscripts\2020_someorigins\Results\cluster_options\%method_%s" % region_column
files = glob.glob(os.path.join(cluster_folder, "*users.csv"))

#get index and post count from a file with results for all users...
refdata = pd.read_csv(os.path.join(r"./demo_results/basic_maxposts_35users.csv"), sep=";")

# Create dataframe for results with userids as index
results = pd.DataFrame(index=refdata["userid"])

for csv in files:
    data = pd.read_csv(csv, sep=";")
    data.index = data[data.columns[-2]]

    print("adding result from ", data.columns[-2])
    results = results.join(data[data.columns[-1]])

# How many times the result was different among methods
print(results.nunique(axis=1).value_counts())

# write all dbscan results with different max distance to file
results.to_csv(os.path.join(cluster_folder, "dbscan_results_with_different_max_distance.csv"), sep=";")

# ------------------------
# Read in expert assesment
# -------------------------
fp = r"P:\h510\some\manuscripts\2020_someorigins\Results\expert_assesment\origin_assesment_expert_1_expert_2.csv"
experts = pd.read_csv(fp, sep=";")

# Get only those rows where experts agree
experts = experts[(experts["expert_1"] == experts["expert_2"]) == True]

# World regions
#fp = r"P:\h510\some\manuscripts\2020_someorigins\Data\Globl_regions_WGS84_7a_projOK.shp"
fp = r"P:\h510\some\manuscripts\2020_someorigins\Data\FIPS_RegCode_SubReg_2.csv"
#world = gpd.read_file(fp)
world = pd.read_csv(fp)

# Take country codes (FIPS) and matching region codes, drop duplicate FIPS
country_codes = world[["FIPS", "RegCode", "SubReg_2"]].drop_duplicates(subset=['FIPS'])

# Move userid as index
experts.index = experts["userid"]

if region_column is not "FIPS":
    region_dict = dict(country_codes[["FIPS", region_column]].values)

    # Set region codes as expert assesment
    experts = experts.replace(region_dict)

# Join experts and cluster results
joined = experts.merge(results, left_index=True, right_index=True, how="left")
joined.to_csv(os.path.join(cluster_folder, "experts_and_dbscan_origins.csv"), sep=";", index=False)


#-------------------------------------------------------
# Check which treshold match best with expert assesment
#-------------------------------------------------------

#Double check that it's correct amount of columns!
print(joined.columns[3:])
print(len(joined.columns[3:]))

# Expert 1 and 2 are the same, doesn't matter which one is compared here
matches = joined[joined.columns[3:]].eq(joined["expert_1"], axis=0)

# Summarize matches
percentages = matches.sum().sort_values(ascending=False) / len(matches)
matches.sum().sort_values(ascending=False)
percentages.map('{:.2%}'.format)

# Messy piece of code for cleaning up the result file for plotting..

# Print % of correct to file
newcol = method + "_" + region_column
perc = pd.DataFrame(percentages, columns=[method + "_" + region_column])
perc["method"] = perc.index
perc["km"] = perc.apply(lambda x: x["method"].split("_")[2], axis=1)
#perc["km"] = perc.apply(lambda x: x["km"][:-2], axis=1)

perc.set_index("km", drop=True, inplace=True)

perc.drop(columns=["method"], inplace=True)

perc.to_csv(os.path.join(output_folder, "matches_%s_%s.csv" % (method, region_column)),
                                        index_label="km", header="perc")