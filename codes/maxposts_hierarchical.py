# -*- coding: utf-8 -*-
"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - MAXPOSTS - HIERARCHICAL


Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA using a spatially hierarchical approach.
The script calculates following things:
    - For each post, specify if it is within or outside the target area (Kruger national Park).
    - Exclude posts within target area from further analysis
    - For each user, calculate
        a) the continent with most posts
        b) within that continent, the region with most posts, and
        c) within that region, the country with most posts
    - Create an output file with probable home country, subregion and region for each user
    - Create an output file for regions, subregions and countries with number of home locations

Data:
    Input: Entire posting history of social media users who have visited the target area (visitors to Kruger national park in 2014)
    Input demo_data should already have information about the continent, subregion and country of origin.

License:
    Creative Commons BY 4.0. See details from https://creativecommons.org/licenses/by/4.0/

Usage:
    Check input files and run the code. Check printout messages!

"""

import geopandas as gpd
import pandas as pd
import os, sys
from fiona.crs import from_epsg


#------------------------
# Functions
#------------------------
def homelocation_maxposts(in_df, regioncolname, index = 1):
    """Return the region with most posts (or 2nd most posts etc.) and associated photocount"""
    # Create index for accessing the correct position among potential homelocations
    i= index - 1

    # List number of posts per region:
    value_counts = in_df[regioncolname].value_counts()

    # get the region with most posts, 2nd mosts posts etc. depending on the index
    try:
        region, photo_cnt = value_counts.index[i], value_counts[value_counts.index[i]]

    except:
        region, photo_cnt = "N/A", 0

    #Return the region and associated photo count:
    return region, photo_cnt

def checkTop2homes(inDF, regioncol1, regioncol2):
    """ Check if the 1st and 2nd most probable home locations have the same amount of posts"""
    test = inDF[regioncol1] == inDF[regioncol2]
    print("Users with two candidates for home location:")
    print(test.value_counts())  #check output

    if len(test.value_counts()) > 1:
        print("check for conflict in", regioncol1, " & ", regioncol2, "!")

    else:
        print("No users with equal amount of posts in",regioncol1, " & ", regioncol2)


def aggregateRegionInfo(usershomelocations, region_column):
    """Return a dataframe with number of home locations per region"""
    homeRegionMatrix = pd.DataFrame()
    value_counts = usershomelocations[region_column].value_counts()

    # Iterate over values and produce DataFrame for country visitor numbers
    for region, cnt in zip(value_counts.index, value_counts.values):
        homeRegionMatrix = homeRegionMatrix.append([[region, cnt]])

    homeRegionMatrix.columns = [region_column, region_column + "_visitorcount"]

    return homeRegionMatrix

def joinHomeLocWithCountryShape(region_matrix, region_column, region_shape):
    """ join number of home locations per region with spatial demo_data"""
    region_join = region_shape.merge(region_matrix, how='outer', left_on= region_column, right_on = region_column + "1_basic")

    #Fill Nan
    region_join[region_column + "1_basic_visitorcount"] = region_join[region_column + "1_basic_visitorcount"].fillna(value=0)
    return region_join


# set method name
method_name = "hierarchical_maxposts"

#--------------------------
# SOCIAL MEDIA DATA
#--------------------------
# Social media mobility history for Kruger national park visitors, with regioninfo, each point is assigned to the nearest region if found not on land
fp = r"./../demo_data/fake_input_data.shp"

#read demo_data with geopandas
some = gpd.read_file(fp)

# Print layer info
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique())

# -----------------------------------
# Posts within Kruger
# -----------------------------------

# EXCLUDE POSTS WITHIN KRUGER NATIONAL PARK (ASSUME NO ONE LIVES THERE..even though in fact people do live there..)
some = some[some["FromKruger"]==0]

# Print layer info
print("\nAfter excluding posts from Kruger:")
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique(), "\n")

#-------------------------------------------------------
# Detect regions and country with maxposts for each user
#-------------------------------------------------------

# Group by individual users
grouped = some.groupby('userid')

# Create GeoDataFrame for the results
geo = gpd.GeoDataFrame(crs=from_epsg(4326), columns = ['userid', 'post_cnt', 't_bef_KNP', 'time_dif', "FIPS_1",
                                                       "FIPS_1_photocount", "FIPS_2", "FIPS_2_photocount",
                                                       "SubReg_2_1", "SubReg_2_1_photocnt", "RegCode_1",
                                                       "RegCode_1_photocnt","RegCode_2", "RegCode_2_photocnt",
                                                       "SubReg_2_2", "SubReg_2_2_photocnt"])

# Number of posts for each user
for userid, data in grouped:
    # Get userid and number of posts
    geo.loc[userid, "userid"] = userid
    geo.loc[userid, "post_cnt"] = len(data)

# REGION/CONTINENT with maxposts for each user using the basic approach
# (list also the second most visited region for accuracy assesment)
for userid, data in grouped:
    # DETERMINE CONTINENT/LARGER REGION with 1st and 2nd most posts
    geo.loc[userid, ["RegCode_1", "RegCode_1_photocnt"]] = homelocation_maxposts(data, "RegCode", 1)
    geo.loc[userid, ["RegCode_2", "RegCode_2_photocnt"]] = homelocation_maxposts(data, "RegCode", 2)

# Check if there were any regions with equal amount of posts for some user
checkTop2homes(geo, "RegCode_1","RegCode_2")

# SUBREGION (within top continent)
for userid, data in grouped:
    # SELECT POST WITHIN THE CONTINENT WITH MOST POSTS
    data = data[data["RegCode"] == geo.loc[userid, "RegCode_1"]]

    # DETERMINE REGION with 1st and 2nd most posts
    geo.loc[userid, ["SubReg_2_1", "SubReg_2_1_photocnt"]] = homelocation_maxposts(data, "SubReg_2", 1)
    geo.loc[userid, ["SubReg_2_2", "SubReg_2_2_photocnt"]] = homelocation_maxposts(data, "SubReg_2", 2)

# Check if there were any regions with equal amount of posts for some user
checkTop2homes(geo, "SubReg_2_1", "SubReg_2_2")

# COUNTRIES (within top subregion)
for userid, data in grouped:
    # SELECT POST WITHIN THE REGION WITH MOST POSTS
    data = data[data["SubReg_2"] == geo.loc[userid, "SubReg_2_1"]]

    # DETERMINE COUNTRY with 1st and 2nd most posts
    geo.loc[userid, ["FIPS_1", "FIPS_1_photocount"]] = homelocation_maxposts(data, "FIPS",1)
    geo.loc[userid, ["FIPS_2", "FIPS_2_photocount"]] = homelocation_maxposts(data, "FIPS", 2)

# Check if there were any regions with equal amount of posts for some user
checkTop2homes(geo, "FIPS_1", "FIPS_2")

# Reset index
geo = geo.reset_index(drop=True)

# save the userlist with home country info in a file:
homelocs = geo[['userid', 'post_cnt', 't_bef_KNP', 'time_dif', 'FIPS_1', 'FIPS_1_photocount', 'FIPS_2',
                'FIPS_2_photocount', 'SubReg_2_1','SubReg_2_1_photocnt', 'RegCode_1', 'RegCode_1_photocnt',
                'RegCode_2', 'RegCode_2_photocnt', 'SubReg_2_2','SubReg_2_2_photocnt']]

homelocs[method_name] = homelocs["FIPS_1"]


homelocs.to_csv(r"./../demo_results/%s_%susers.csv" % (method_name, str(homelocs.userid.nunique())), sep=";")

#------------------------------
# Aggregate results by region
#-----------------------------
# Calculate "home location" statistics for each regional unit
country_matrix = aggregateRegionInfo(geo, 'FIPS_1')

# Rename column for output
country_matrix.rename(columns={"FIPS_1_visitorcount": method_name}, inplace=True)

#subregion_matrix = aggregateRegionInfo(geo, 'SubReg_1')# not calculated!
subregion2_matrix = aggregateRegionInfo(geo, 'SubReg_2_1')
continent_matrix = aggregateRegionInfo(geo, 'RegCode_1')

country_matrix.to_csv(r"./../demo_results/%s_%susers_by_country.csv" % (method_name, str(homelocs.userid.nunique())),
                      index=False, sep=";")








