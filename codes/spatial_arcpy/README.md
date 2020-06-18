Centrographic methods (median center, mean center, ellipse centroid, circle centroid ) were implemented using the
arcpy module in Python 2.7 via ArcMap 10.3. Intermediate processing (scripts 2b and 3) are implemented in Python 3.7 using pandas and geopandas modules. Tested to work with the fake input data in June 2020. 

If running these files please note file-paths to folders for storing intermediate results 
(not all intermediate data is included in this repository).


For the basic approach (all methods), run the files in this order:

- 1a (clusters based on the whole data)
- 2a (join region info)
- 3  (print results to csv)

For the hierarchical approach (all methods), run the files in this order:

- 1a (clusters based on the whole data)
- 2a (join region info to centroids)
- 2b (get subset of data for each users from the continent where the centroid was located base on each method)
- 1b (cluster based on data from top continent)
- 2a (join region info to centroids)
- 2b (get subset of data for each user from the subregion where the centroid was located base on each method)
- 1b (cluster based on data from top subregion)
- 2b (join region info to centroids)
- 3 (print results to csv)
