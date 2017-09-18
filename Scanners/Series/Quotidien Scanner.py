# -*- coding: utf-8 -*-

import re, os, os.path
import sys
#import locale
import datetime
#locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# I needed some plex libraries, you may need to adjust your plex install location accordingly
#sys.path.append("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Scanners/Series")
#sys.path.append("/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins/Scanners.bundle/Contents/Resources/Common/")
import Media, Stack, Utils, VideoFiles
from mp4file import mp4file, atomsearch


### Log + LOG_PATH calculated once for all calls ###
import logging, logging.handlers                        #
RootLogger     = logging.getLogger('main')
RootHandler    = None
RootFormatting = logging.Formatter('%(message)s') #%(asctime)-15s %(levelname)s - 
RootLogger.setLevel(logging.DEBUG)
Log             = RootLogger

FileListLogger     = logging.getLogger('FileListLogger')
FileListHandler    = None
FileListFormatting = logging.Formatter('%(message)s')
FileListLogger.setLevel(logging.DEBUG)
LogFileList = FileListLogger.info

def set_logging(instance, filename):
  global RootLogger, RootHandler, RootFormatting, FileListLogger, FileListHandler, FileListFormatting
  logger, handler, formatting, backup_count = [RootLogger, RootHandler, RootFormatting, 9] if instance=="Root" else [FileListLogger, FileListHandler, FileListFormatting, 1]
  if handler: logger.removeHandler(handler)
  handler = logging.handlers.RotatingFileHandler(os.path.join(LOG_PATH, filename), maxBytes=10*1024*1024, backupCount=backup_count)    #handler = logging.FileHandler(os.path.join(LOG_PATH, filename), mode)
  handler.setFormatter(formatting)
  handler.setLevel(logging.DEBUG)
  logger.addHandler(handler)
  if instance=="Root":  RootHandler     = handler
  else:                 FileListHandler = handler


### Check config files on boot up then create library variables ###    #platform = xxx if callable(getattr(sys,'platform')) else "" 
import inspect
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "..", "..", "Logs"))
if not os.path.isdir(LOG_PATH):
  path_location = { 'Windows': '%LOCALAPPDATA%\\Plex Media Server',
                    'MacOSX':  '$HOME/Library/Application Support/Plex Media Server',
                    'Linux':   '$PLEX_HOME/Library/Application Support/Plex Media Server' }
  try:  path = os.path.expandvars(path_location[Platform.OS.lower()] if Platform.OS.lower() in path_location else '~')  # Platform.OS:  Windows, MacOSX, or Linux
  except: pass #os.makedirs(LOG_PATH)  # User folder on MacOS-X
LOG_FILE_LIBRARY = LOG_FILE = 'Plex Media Scanner (Quotidien).log'                # Log filename library will include the library name, LOG_FILE not and serve as reference
set_logging("Root", LOG_FILE_LIBRARY)


__author__ = "Ralmn"
__copyright__ = "Copyright 2017"
__credits__ = ["Ralmn"]

__license__ = "GPLv2"
__version__ = "1.0"
__maintainer__ = "Ralmn"
__email__ = ""


episode_regexps = [
'_(?P<part>\w+)_partie_du_(?P<day>[0-9]+)_(?P<month>[a-z]+)_(?P<year>[0-9]+)'
]

# date_regexps = [
#     '(?P<year>[0-9]{4})[^0-9a-zA-Z]+(?P<month>[0-9]{2})[^0-9a-zA-Z]+(?P<day>[0-9]{2})([^0-9]|$)',           # 2009-02-10
#     '(?P<month>[0-9]{2})[^0-9a-zA-Z]+(?P<day>[0-9]{2})[^0-9a-zA-Z(]+(?P<year>[0-9]{4})([^0-9a-zA-Z]|$)',    # 02-10-2009
#   ]

# standalone_episode_regexs = [
#   '(.*?)( \(([0-9]+)\))? - ([0-9]+)+x([0-9]+)(-[0-9]+[Xx]([0-9]+))?( - (.*))?',         # Newzbin style, no _UNPACK_
#   '(.*?)( \(([0-9]+)\))?[Ss]([0-9]+)+[Ee]([0-9]+)(-[0-9]+[Xx]([0-9]+))?( - (.*))?'      # standard s00e00
#   ]

# season_regex = '.*?(?P<season>[0-9]+)$' # folder for a season

# just_episode_regexs = [
#     '(?P<ep>[0-9]{1,3})[\. -_]of[\. -_]+[0-9]{1,3}',       # 01 of 08
#     '^(?P<ep>[0-9]{1,3})[^0-9]',                           # 01 - Foo
#     'e[a-z]*[ \.\-_]*(?P<ep>[0-9]{2,3})([^0-9c-uw-z%]|$)', # Blah Blah ep234
#     '.*?[ \.\-_](?P<ep>[0-9]{2,3})[^0-9c-uw-z%]+',         # Flah - 04 - Blah
#     '.*?[ \.\-_](?P<ep>[0-9]{2,3})$',                      # Flah - 04
#     '.*?[^0-9x](?P<ep>[0-9]{2,3})$'                        # Flah707
#   ]

# ends_with_number = '.*([0-9]{1,2})$'

# ends_with_episode = ['[ ]*[0-9]{1,2}x[0-9]{1,3}$', '[ ]*S[0-9]+E[0-9]+$']

# Look for episodes.
def Scan(path, files, mediaList, subdirs):
  Log.debug( "Quotidien scanning")
  # Scan for video files.
  VideoFiles.Scan(path, files, mediaList, subdirs)
  
  # Take top two as show/season, but require at least the top one.
  paths = Utils.SplitPath(path)
  
  # if len(paths) > 0 and len(paths[0]) > 0:
  #   done = False

  #   if done == False:

  #     # Not a perfect standalone match, so get information from directories. (e.g. "Lost/Season 1/s0101.mkv")
  #     season = None
  #     seasonNumber = None

  #     (show, year) = VideoFiles.CleanName(paths[0])
      
  for i in files:
    done = False
    file = os.path.basename(i)
    (file, ext) = os.path.splitext(file)

    #(show, year) = VideoFiles.CleanName(file)
    show = "Quotidien"

    Log.debug('File: %s, show: %s' %(file, show))
    
    
    # Test for matching tivo server files
    found = False
    for rx in episode_regexps:
      match = re.search(rx, file, re.IGNORECASE | re.UNICODE)
      if match:
        originalAirDate = None
        part = str(match.group('part')) if match.group('part') and match.group('part') != '' else None
        day = int(match.group('day')) if match.group('day') and match.group('day') != '' else None
        month = str(match.group('month')) if match.group('month') and match.group('month') != '' else None
        year = int(match.group('year')) if match.group('year') and match.group('year') != '' else None
        
        

        if 'deuxieme' in part:
          part = '2'
          part_str = 'Deuxieme'
        else:
          part = '1'
          part_str = 'Premiere'

        title = '%s partie du %s %s %s' % (part_str, day, month, year)

        DATE_FORMAT = "%d %B %Y"
        date_txt = "%s %s %s" %(day, month, year)
        #date = datetime.datetime.strptime(date_txt, DATE_FORMAT)

        month_num = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin', 'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre' ].index(month) + 1
        episode = "%s%s" % (day, part)
        season = "%s%s" % (year, month_num)


        found = True

        tv_show = Media.Episode(show, season, episode, title, None)

        originalAirDate = datetime.date(int(year), int(month_num), int(day))

        if originalAirDate is not None:
          tv_show.released_at = originalAirDate

        tv_show.parts.append(i)
        mediaList.append(tv_show)
        if found == True:
          continue

          if done == False:
            Log.debug("Got nothing for:", file) 

  # Stack the results.
  Log.debug('mediaList : %s' % mediaList)
  Stack.Scan(path, files, mediaList, subdirs)

def find_data(atom, name):
  child = atomsearch.find_path(atom, name)
  data_atom = child.find('data')
  if data_atom and 'data' in data_atom.attrs:
    return data_atom.attrs['data']

if __name__ == '__main__':
  Log.debug( "Start quotidien scanner args: " % sys.argv)
  path = sys.argv[1]
  files = [os.path.join(path, file) for file in os.listdir(path)]
  media = []
  Scan(path[1:], files, media, [])
  Log.debug ("Media:", media)
