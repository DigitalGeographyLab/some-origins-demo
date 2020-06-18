"""

Code associated to following manuscript:
    "Identifying the origins of social media users."

script for repeating the DBSCAN clustering with different search distances (esp). Values are in kilometers.

"""

import sys
import os

tool_name = "clusters_hierarchical.py" # "clusters_basic.py" #

python_folder = r"C:\Hyapp\Anaconda3-2019.3\envs\gis"
#python_folder = r"C:\HYapp\Anaconda3\envs\autogis"

python_path = os.path.join(python_folder, "python.exe")

# Repeat the process
for distance in [1, 10, 25, 60, 120, 210, 340, 500, 725, 1000]:
    print("\n--------------------------------------------------")
    print("Clustering the demo_data using {0} km as min distance".format(distance))

    # Call for the script and set distance as command line argument
    # For some stupid reason, have to manually define interpreter here for the subprocess...
    #os.system(r"{0} {1} {2} {3}".format(python_path, tool_name, distance, n_points))
    os.system(r"{0} {1} {2}".format(python_path, tool_name, distance))

