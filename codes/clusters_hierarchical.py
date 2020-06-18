# -*- coding: utf-8 -*-
"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

SOMEORIGINS - DBSCAN clustering

https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html

Script for identifying the most probable home country for Instagram users that have visited Kruger national park, SA.
The script does the following things:


HIERARCHICAL

- For each user, detect
    a) the continent with biggest cluster and asses best max_threshold
    b) within that continent the region with biggest cluster and asses best max_threshold
    c) within that region the country with biggest cluster and asses best max_threshold


1. Read input demo_data
    - All posts from all users who visited Kruger in 2014
        --> Exclude posts within target area (Kruger) from further analysis
2. Get clusters for each user using DBSCAN
    --> Find centermost point for each cluster (Using G. Boeing's approach). This makes the code a bit slow, but more logical?
    --> Join info about country /region / continent to cluster center points
    --> Find biggest cluster(s) for each user
4. Determine origin continent based on biggest cluster
    --> cluster again only considering points from the continent (repeat step 2)
5. Determine sub-region
    --> cluster again considering points from the continent (repeat step 2)
6. Determine origin country based on the location of biggest cluster(s).
    --> if there are equally big clusters in several countries, pick the country with most clusters (?)
7. Print origin country to file by user and by region


Data:
     Input: Entire posting history of social media users who have visited the target area (visitors to Kruger national park in 2014)
     Input demo_data should already have information about the continent, subregion and country of origin.


References:
    Radian conversion, and finding centermost point in cluster: G. Boeing 2018 https://arxiv.org/pdf/1803.08101.pdf

Created on:
    Tue Feb 25 2020

License:
    Creative Commons BY 4.0. See details from https://creativecommons.org/licenses/by/4.0/

    NOTE! Geopy Point requires the coordinates in latitude (y), longitude (x) order!
    https://geopy.readthedocs.io/en/1.14.0/#geopy.point.Point


usage:
    python clusters_basic.py min_distance min_points

    min distance in km determines the epsilon for DBSCAN. If min_istance is not defined, it defaults to 1.
    If min_points is not defined, it defaults to 1.
"""
import pandas as pd
import geopandas as gpd
import os
import sys
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Point, MultiPoint
from geopy.distance import great_circle
import matplotlib.pyplot as plt


#sns.set_style("whitegrid")

def cluster_points(geom_column, min_distance_in_km, n_posts=1):
    """ Applies DBSCAN clustering method on a set of points using haversine (great-circle) distance. 
    Noisy samples are given the label -1.

    Uses: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html#sklearn.cluster.DBSCAN.fit
    Haversine distance calculation following G. Boeing 2018 https://arxiv.org/pdf/1803.08101.pdf

    :param geom_column: Geopandas GeoSeries that contains point geometries as Shapely points (geometry column).
    :param min_distance_in_km: minimum distance in kilometers.
    :param n_posts: Minimum number of points per cluster. if 1 (default), there will be no outliers.
    :return: DBSCAN cluster labels as a Pandas Series
    """
    kms_per_radian = 6371.0088
    epsilon = min_distance_in_km / kms_per_radian

    # Prepare geometry column into the correct format
    # NOTE! in shapely points, x=longitude (east-west), y=latitude (north-south).
    # In the Haversine distance calculation;
    # "the first distance of each point is assumed to be the latitude, the second is the longitude, given in radians."
    # So, we create a list of coordinate pairs in the order [latitude, longitude] / [Point.y, Point.x]
    coords_list = list(zip(geom_column.y, geom_column.x))

    # Get clusters using DBSCAN:
    # https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html#sklearn.cluster.DBSCAN.fit
    # Settings adapted from G. Boeing 2018 https://arxiv.org/pdf/1803.08101.pdf
    clustering = DBSCAN(eps=epsilon,
                        min_samples=n_posts,
                        algorithm='ball_tree',
                        metric='haversine').fit(np.radians(coords_list))

    return clustering.labels_


def get_centermost_point(points_in_cluster):
    """Get the point in a cluster which is closest to the geographic cluster centroid.
    Adapted from G. Boeing 2018 https://arxiv.org/pdf/1803.08101.pdf

    :param points_in_cluster: Geopandas GeoSeries that contains point geometries of the cluster as Shapely points (the geometry column of one cluster)
    :return: Shapely point that contains the geometry (x, y) / (longitude, latitude) of the most central point
    """

    # Define cluster centroid (might be that none of the points is located exactly here).
    centroid = Point(MultiPoint(points_in_cluster.to_list()).centroid.x, MultiPoint(points_in_cluster.to_list()).centroid.y)

    # Define point closest to cluster centroid (following G. Boeing 2018).
    # NOTE: geopy great circle takes in coordinates in the order latitude, longitude (y,x),
    #       so here we zip them in a different order than before!!
    cluster_coords = list(zip(points_in_cluster.y, points_in_cluster.x))
    centermost_y, centermost_x = min(cluster_coords, key=lambda point: great_circle(point, (centroid.y, centroid.x)).m)

    # Convert coordiantes to a shapely point Point(lon, lat)
    centermost_point = Point(centermost_x, centermost_y)

    return centermost_point

def get_origin_country(clusters_df, reg_col='FIPS'):
    """ Determine which country has most clusters in case of many candidates

    :param clusters_df: demo_data frame with biggest cluster(s), with a column for region info.
    :param reg_col: column to use to summarize number of points (default: "FIPS": per country code)
    :return: country code (str) or a list of country codes
    """

    # Check if there are more than one clusters with the largest number of posts
    if len(clusters_df) > 1:

        # Number of clusters per country (can be one country or many countries)
        value_counts = clusters_df[reg_col].value_counts()

        # Check if there are more than one countries listed 
        if len(value_counts) > 1:
            
            # Series of countries which had most clusters (can be one country or many countries)
            countries_with_most_clusters = value_counts[value_counts == value_counts.max()]

            # Check if there is more than one country with maximum number of clusters
            if len(countries_with_most_clusters) > 1:
                
                # List countries with equal number of biggest clusters
                orig = list(countries_with_most_clusters.index)

            else: 
                orig = value_counts.idxmax()

        else:
            # In case there is only one country with the largest number of cluster centers
            orig = value_counts.index[0]

    else:
        # If there was only one cluster to begin with
        orig = clusters_df.at[clusters_df.index[0], reg_col]

    return orig

#-----------------------
# Settings
#-----------------------

# minimum distance in kilometers
try:
    max_distance = int(sys.argv[1])

except:
    # 725/500/210 km if not set on command line
    max_distance = 500 #210 # 725

# minimum distance in kilometers
min_points = 1

# First round, RegCode: Continent-level, esp 725 km
#target_region_column = "RegCode"

# for continent-level, there is no upper method
#upper_method_name = ""

# Second round, SubReg_2: subregions
#upper_region_column = "RegCode"
#target_region_column = 'SubReg_2'
#upper_threshold = 725

# SETTINGS FOR SUB-REGION CLUSTERING
upper_region_column = 'SubReg_2'
target_region_column = 'FIPS'
upper_threshold = "210"


#For sub-region and country-detection, we set upper method name to find correct data subset
upper_method_name = "hierarchical_dbscan_%skm_%s" % (upper_threshold, upper_region_column)

# Create column name for final output with info of used min_distance
method_name = "hierarchical_dbscan_%skm_%s" % (max_distance, target_region_column)

# --------------------------
# Read in demo_data
# --------------------------
print("Reading demo_data..")

# Social media mobility history for Kruger national park visitors, with regioninfo
#each point is assigned to the nearest region if found not on land. Also duplicates have been removed
fp = r"./demo_data/fake_input_data.shp"

#read demo_data with geopandas
some = gpd.read_file(fp)

# Print layer info
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique())

# EXCLUDE POSTS WITHIN KRUGER NATIONAL PARK (ASSUME NO ONE LIVES THERE..even though in fact people do live there..)
some = some[some["FromKruger"] == 0]

# Print layer info
print("\nAfter excluding posts from Kruger:")
print("Number of posts:", len(some))
print("Number of users:", some.userid.nunique(), "\n")


# HIERARCHICAL APPROACH: SUBSET EACH USER FOR IDENTIFIED REGION
if upper_method_name != "":
    region_folder = r"./demo_results/clusters_temp"
    region_fp = os.path.join(region_folder, "%s_35users.csv") % upper_method_name

    regions = pd.read_csv(region_fp, sep=";")

    regions["userid"] = regions["userid"].astype(str)
    regions[upper_method_name] = regions[upper_method_name].astype(int)

    # Join the demo_data. drops out un-matching rows!
    some = some.merge(regions, left_on=["userid", upper_region_column], right_on=["userid", upper_method_name])

    print("\nAfter subsetting to region:")
    print("Number of posts:", len(some))
    print("Number of users:", some.userid.nunique(), "\n")

# -----------------------------------
# Get clusters for all users
# -----------------------------------
print("Getting clusters..")

# add new column for cluster labels 
some["cluster"] = ""

# Group by userid
grouped = some.groupby("userid")

# For each user, detect clusters
for key, group in grouped:

    clusters = cluster_points(group.geometry, min_distance_in_km=max_distance, n_posts=min_points)
    some.loc[some["userid"] == key, "cluster"] = clusters

# --------------------------------------
# Get most central point for each cluster
# --------------------------------------
print("Finding most central point for each cluster..(this takes a few moments)")

# Group by user AND cluster
grouped = some.groupby(["userid", "cluster"])

# DataFrame for cluster info
cluster_results = gpd.GeoDataFrame(index=grouped.groups.keys())
cluster_results["geometry"] = ""

# For each cluster, find the most central point
for key, group in grouped:
    
    # Add info of cluster size
    cluster_size = len(group)
    cluster_results.loc[key, "cluster_size"] = cluster_size

    # Find the point that is closest to the geographic center of the cluster
    centermost_point = get_centermost_point(group["geometry"])

    # Not used at the moment..
    #centermost_point = get_cluster_centroid(group["geometry"])

    # Add point closest to cluster centroid to geodataframe as a shapely point
    cluster_results.loc[key, "geometry"] = centermost_point

# --------------------------------------
# Find biggest cluster for each user
# --------------------------------------
print("Finding each user's biggest cluster..")

# add userid and cluster code into own column (just because multi index is a bit complex to grasp..) 
cluster_results["userid"] = cluster_results.index.get_level_values(0)
cluster_results["cluster_code"] = cluster_results.index.get_level_values(1)

grouped = cluster_results.groupby("userid")

# Biggest cluster per user
#grouped.cluster_size.max()

for key, group in grouped:
    # Get size of the biggest cluster for this user (could be multiple clusters..)
    biggest_cluster_size = group.cluster_size.max()

    # Find rows for this user in the cluster results which represent this user's largest cluster (could be multiple)
    condition = (cluster_results["userid"] == key) & (cluster_results["cluster_size"] == biggest_cluster_size)
    cluster_results.loc[condition, "largest_cluster"] = True

# Check how many users have more than one biggest cluster )
#cluster_results.groupby("userid").largest_cluster.count().value_counts()

# -------------------------------
# Join region info to clusters
# ------------------------------
print("Joining region info to cluster centers..")

# Here we join the region info of the original some layer, where points are liked with the nearest polygon on land

# Both layer geometries are in WGS 84, but the crs definitions don't yet match
cluster_results.crs = some.crs

# update cluster results index for the join..
cluster_results.index = cluster_results.apply(lambda x: x["userid"] + "_" + str(x["cluster_code"]), axis=1)

# Join country info for each post
clusters = gpd.sjoin(cluster_results, some[["FIPS", "RegCode",  "SubReg_2", "geometry"]], how="left", op="intersects")

# ---------------------------------------------------------------------------------
# Determine origin country for users based on location of (1-x) biggest cluster(s)
# ---------------------------------------------------------------------------------

print("Determining origin country..")
user_list = pd.DataFrame(index=some.userid.unique())

# Group clusters per user (all clusters are still included at this step)
grouped = clusters.groupby("userid")

# For each user, check the location of biggest cluster(s) and decide origin country
for key, group in grouped:

    # Continue with only the biggest cluster(s) (can be one or many)
    largest_clusters = group[group["largest_cluster"] == True]

    # Get origin region (can also be a list of regions if unambiguous
    origin_country = get_origin_country(largest_clusters, reg_col=target_region_column)

    # If there is a list of potential origin countries, apply additional rules:
    if type(origin_country) == list:
        clusters_in_candidate_countries = group[group[target_region_column].isin(origin_country)]

        # if the previous step returned more than one options, consider also other clusters in these countries
        origin_country = get_origin_country(clusters_in_candidate_countries, reg_col=target_region_column)
        
        # If there still are more than one candidates, then determine based on post count in clusters
        if type(origin_country) == list:
            cluster_point_counts_per_country = clusters_in_candidate_countries.groupby(target_region_column).cluster_size.sum()

            if len(cluster_point_counts_per_country):
                origin_country = cluster_point_counts_per_country.idxmax()

            else:
                origin_country = list(cluster_point_counts_per_country.index)
            
    user_list.at[key, method_name] = origin_country

# ------------------------------
# Write result to file by user
# ------------------------------
print("Writing results with min_distance %s.." % max_distance)

# Drop users with no result
user_list = user_list.dropna()

#set folder
#folder = r"./demo_results/clusters_temp/hierarchical_%s" % target_region_column

if target_region_column=="FIPS":
    folder = r"./demo_results/"

else:
    folder = r"./demo_results/clusters_temp"

fp_by_users = os.path.join(folder, "%s_%susers.csv" % (method_name, str(len(user_list))))
user_list.to_csv(fp_by_users, sep=";", index=True, index_label="userid")

# -------------------------------
# Write result to file by country
fp_by_region = os.path.join(folder, "%s_%susers_by_country.csv" % (method_name, str(len(user_list))))

user_list[method_name].value_counts().to_csv(fp_by_region, sep=";",
                                             index_label=target_region_column, header=[method_name])
