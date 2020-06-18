"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

Code for harmonizing and joining together results from different methods into one file
    - by users
    - by countries
"""
import os
import glob
import pandas as pd
import geopandas as gpd

# Results by user
in_folder = r"./demo_results"
files = glob.glob(os.path.join(in_folder,"*users.csv"))

#get index and post count from a file with results for all users...
refdata = pd.read_csv(os.path.join(in_folder, "basic_maxdays_35users.csv"), sep=";")

# Create dataframe for results with userids as index
results = pd.DataFrame(index=refdata["userid"])

for csv in files:
    data = pd.read_csv(csv, sep=";")
    data.index = data["userid"]
    results = results.join(data[data.columns[-1]])


codes_fp = "country_codes.csv"
codes = pd.read_csv(codes_fp, sep=";")
country_dict = codes.set_index("country", drop=True).to_dict()

"""

# EXPERT ASSESMENT:
folder = r"valid_results"
files = glob.glob(os.path.join(folder,"*430_users_expert_*csv"))



number = 1
for csv in files:
    expert = pd.read_csv(csv, sep=";")
    expert = expert[["userid", "country"]]
    expert.set_index("userid", inplace=True, drop=True)
    expert.replace({"country": country_dict["FIPS"]}, inplace=True)
    expert.rename(columns={"country": "expert_%s" % number}, inplace=True)
    
    results = results.merge(expert, left_index=True, right_index=True, how="left")
    number = number + 1
"""

# Rename columns
results.columns = results.columns.str.replace("hierarchical", "H")
results.columns = results.columns.str.replace("HIERARCHICAL2", "H")
results.columns = results.columns.str.replace("basic", "B")
results.columns = results.columns.str.replace("BASIC", "B")
results.columns = results.columns.str.replace("_FIPS", "")

# Write results by user to file
results.to_csv(r"./demo_results/results_combined_by_user.csv", sep=";",
               index=True,
               index_label="userid")

# Write expert assesment results into a separate file..
#expert_file = results[["expert_1", "expert_2"]].dropna()
#expert_file.to_csv(r"origin_assesment_expert_1_expert_2.csv", sep=";", index=True, index_label = "userid")


#REGIONAL RESLUTS
folder = r"./demo_results"
files = glob.glob(os.path.join(folder, "*country.csv"))

# Create output file for results
regionresults = pd.DataFrame(index=codes["FIPS"].unique())

for csv in files:
    data = pd.read_csv(csv, sep=";")
    
    if "FIPS_1" in data.columns.values:
        data.index = data["FIPS_1"]
    else: 
        data.index=data["FIPS"]

    regionresults = regionresults.merge(data[[data.columns[-1]]], left_index=True, right_index=True, how="left")

# Rename columns
regionresults.columns = regionresults.columns.str.replace("hierarchical", "H")
regionresults.columns = regionresults.columns.str.replace("HIERARCHICAL2", "H")
regionresults.columns = regionresults.columns.str.replace("basic", "B")
regionresults.columns = regionresults.columns.str.replace("BASIC", "B")
regionresults.columns = regionresults.columns.str.replace("_FIPS", "")

# Save region results to file
regionresults.to_csv(r"./demo_results/results_combined_by_region.csv",
                     sep=";",
                     index=True,
                     index_label="FIPS")


print("DONE!")