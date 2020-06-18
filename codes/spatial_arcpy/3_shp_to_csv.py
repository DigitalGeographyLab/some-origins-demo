"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

Run this code after runnign 2a for the whole data or subregions

Convert shapefiles to csv files
- by user
- by region
"""
import glob
import geopandas as gpd
import os


input_folder = r"./demo_results/spatial_temp"
method_type ="basic_"

#input_folder = r"./demo_results/spatial_temp/hierarchical_subreg"
#method_type ="hierarchical_"

user_results_folder = r"./demo_results"
country_folder = r"./demo_results"

files = glob.glob(os.path.join(input_folder, "*Regioninfo.shp"))

for shp in files:
    data = gpd.read_file(shp)
    data = data[[ 'userid','Country', 'Cntry_code', 'FIPS', 'RegioName', 'RegCode',
       'SubregCode', 'OriginUnit', 'SubReg_2']]

    method = method_type + os.path.basename(shp).split("_")[0]
    method_details = method_type + os.path.basename(shp).split("_")[0] + "_" + str(data.userid.nunique()) + "users"
    print(method_details)


    data[method] = data["FIPS"]

    data[["userid", method]].to_csv(os.path.join(user_results_folder, method_details +".csv"), sep=";", index=False)
    data["FIPS"].value_counts().to_csv(os.path.join(country_folder, method_details + "_by_country.csv"),
                                       sep=";",
                                       index_label="FIPS",
                                       header=[method])





