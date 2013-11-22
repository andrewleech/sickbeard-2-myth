#!/usr/bin/env python
import _mysql
import sys
import time
import os
import xmltodict
import socket
import logging
import logging.handlers

# This folder needs to be added to new myth storage group called Links
TV_PATH="/myth/tv_downloaded/"
BACKEND_HOST='localhost'
BACKEND_USER='mythtv'
BACKEND_PASS='' # can often be found in /etc/mythtv/config.xml
LOG_PATH='/tmp/sickbeard-2-myth.log'

#logging
FORMAT="%(asctime)-15s : %(message)s"
logHandler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=2*1024*1024, backupCount=2)
logHandler.setFormatter(logging.Formatter(FORMAT))
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
logger.addHandler(logHandler)

try:
    # Expects to be run as extra_script from sickbeard
    # Args: http://code.google.com/p/sickbeard/wiki/AdvancedSettings#Extra_Scripts
    # 1. final full path to the episode file
    # 2. original name of the episode file
    # 3. show tvdb id
    # 4. season number
    # 5. episode number
    # 6. episode air date

    # We only care about the first one

    if len(sys.argv) >= 2:
        finalPath   = sys.argv[1]

    else:
        logger.debug("Must be run as sickbeard extra_script or given > 1 args with filename as first")
        print "Must be run as sickbeard extra_script or given > 1 args with filename as first"
        exit(1)

    if os.path.isfile(os.path.splitext(finalPath)[0]+".nfo"):
        metaFile = None
        metaXml = None
        with open(os.path.splitext(finalPath)[0]+".nfo", 'r') as content_file:
            metaFile = content_file.read()
        if not metaFile:
            logger.debug("Ensure sickbeard is configured to create .nfo metadata file in xbmc format (under post processing settings)")
            print "Ensure sickbeard is configured to create .nfo metadata file in xbmc format (under post processing settings)"
            exit(1)

        else:
            # create symlink in folder in folder to appear in recordings
            if os.path.isfile(os.path.join(TV_PATH, os.path.basename(finalPath))):
                os.unlink(os.path.join(TV_PATH, os.path.basename(finalPath)))
            os.symlink(finalPath, os.path.join(TV_PATH, os.path.basename(finalPath)))

            # Parse data from metadata file
            metaXml = xmltodict.parse(metaFile)

            title = os.path.basename(os.path.dirname(os.path.dirname(finalPath)))

            con = _mysql.connect(BACKEND_HOST, BACKEND_USER, BACKEND_PASS, 'mythconverg')

            #add channel definition if needed
            sql = "select `callsign` from `channel` where `chanid` = '9999' limit 1;"
            con.query(sql)
            try:
                unused = con.use_result().fetch_row()[0][0]
            except IndexError:
                sql = "INSERT INTO `channel` (`chanid`, `channum`, `freqid`, `sourceid`, `callsign`, `name`, `icon`, `finetune`, `videofilters`, `xmltvid`, `recpriority`, `contrast`, `brightness`, `colour`, `hue`, `tvformat`, `visible`, `outputfilters`, `useonairguide`, `mplexid`, `serviceid`, `tmoffset`, `atsc_major_chan`, `atsc_minor_chan`, `last_record`, `default_authority`, `commmethod`, `iptvid`) VALUES(9999, '0', NULL, 0, 'Download', 'Download', '', NULL, '', '', 0, 32768, 32768, 32768, 32768, 'Default', 0, '', 0, 0, 0, 0, 0, 0, '2013-01-01 00:00:00', '', -1, NULL);"
                con.query(sql)

            #add storage group if needed
            sql = "select `dirname` from `storagegroup` where `groupname` = 'Links' limit 1;"
            con.query(sql)
            try:
                unused = con.use_result().fetch_row()[0][0]
            except IndexError:
                sql = "INSERT INTO `storagegroup` (`groupname`, `hostname`, `dirname`) VALUES('Links', '" + socket.gethostname() + "', '" + TV_PATH + "');"
                con.query(sql)

            #get seriesid from database if possible
            sql = "select `seriesid` from `recorded` where `title` = '" + title + "' limit 1;"
            con.query(sql)
            seriesid = 0
            try:
                seriesid = con.use_result().fetch_row()[0][0]
            except KeyError:
                pass

            currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))

            data = [
                9999,   #chanid
                currentTime,   #starttime
                currentTime,   #endtime
                title,   #title
                metaXml['episodedetails']['title'],   #subtitle
                metaXml['episodedetails']['plot'],   #description
                int(metaXml['episodedetails']['season']),   #season
                int(metaXml['episodedetails']['episode']),   #episode
                "",   #category
                socket.gethostname(),   #hostname
                0,   #bookmark
                0,   #editing
                0,   #cutlist
                0,   #autoexpire
                1,   #commflagged
                'Default',   #recgroup
                0,   #recordid
                int(seriesid),   #seriesid
                "",   #programid
                "",   #inetref
                currentTime,   #lastmodified
                os.path.getsize(finalPath),   #filesize
                0,   #stars
                0,   #previouslyshown
                metaXml['episodedetails']['aired'],   #originalairdate
                1,   #preserve
                0,   #findid
                0,   #deletepending
                0,   #transcoder
                1,   #timestretch
                0,   #recpriority
                os.path.basename(finalPath),   #basename
                currentTime,   #progstart
                currentTime,   #progend
                'Default',   #playgroup
                'Default',   #profile
                0,   #duplicate
                1,   #transcoded
                0,   #watched
                'Links',   #storagegroup
                "0000-00-00 00:00:00",   #bookmarkupdate
                ]

            insert = 'INSERT INTO `recorded` (`chanid`, `starttime`, `endtime`, `title`, `subtitle`, `description`, `season`, `episode`, `category`, `hostname`, `bookmark`, `editing`, `cutlist`, `autoexpire`, `commflagged`, `recgroup`, `recordid`, `seriesid`, `programid`, `inetref`, `lastmodified`, `filesize`, `stars`, `previouslyshown`, `originalairdate`, `preserve`, `findid`, `deletepending`, `transcoder`, `timestretch`, `recpriority`, `basename`, `progstart`, `progend`, `playgroup`, `profile`, `duplicate`, `transcoded`, `watched`, `storagegroup`, `bookmarkupdate`) VALUES('
            for item in data:
                insert += "\"" if (isinstance(item, basestring)) else ""
                insert += str(item)
                insert += "\"" if (isinstance(item, basestring)) else ""
                insert += ", "
            insert = insert.strip().strip(",") + ");"

            logger.debug(insert)

            con.query(insert)


except Exception as e:
    logger.debug("Error %d: %s" % (e.args[0], e.args[1]))
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)

finally:
    
    logHandler.close()
    if con:
        con.close()

sys.exit(0)
