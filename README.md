pyFactorioUpdate was created to eliminate the toil involved in updating a 
headless Factorio server. When run the script will compare the last-modified 
header of the Factorio archive available for download against the creation time 
of the most recently downloaded archive, if the web version is newer it will be 
fetched and installed. Using -e or --experimental will compare against the 
experimental version of Factorio rather than the stable version. To force a 
download and installation regardless of timestamps use -f or --force.