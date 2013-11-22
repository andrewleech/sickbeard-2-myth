sickbeard-2-myth
================

Use to add a video file to the recording list on mythtv


Description
============

I often use sickbeard to track tv shows, and decided that while having them in folders in mythtv's video list was best for longevity, I also wanted them to show up in the recordings list when they're first aquired to watch along with everything else that's recorded.
This script accomplishes that.
I use it as extra_scripts in sickbeard (http://code.google.com/p/sickbeard/wiki/AdvancedSettings), but basically run it with the desired video file as the first argument and it should do everything from there.

Requirements
=============
python  
python mysql bindings   (sudo apt-get install python-mysqldb)  
xmltodict               (sudo apt-get install python-pip && pip install xmltodict)  

Configure
==========

At the top of the script there are a few variables

TV_PATH="/myth/tv_downloaded/"  # folder used to store symlinks, not actual videos  
BACKEND_HOST='localhost'  
BACKEND_USER='mythtv'  
BACKEND_PASS=''                 # can often be found in /etc/mythtv/config.xml  
LOG_PATH='/tmp/sickbeard-2-myth.log'  

The script should automatically add a couple of required entries into the mythtv database on first run, after which  mythtv-backend will probably need to be restarted
After that it just adds a new row to the recorded database for each video, which show up the first time you go to the recorded shows screen afterwards.

Cheers,  
Andrew Leech

www.alelec.net  
https://github.com/coronafire/sickbeard-2-myth
