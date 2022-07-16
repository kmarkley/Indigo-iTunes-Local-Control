#! /usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
# iTunes Applescripts
################################################################################

import applescript
import inspect
import os
try:
    import indigo
except:
    pass


mac_base_ver = int(os.popen("sw_vers -productVersion").read().strip().split(".")[0])
if mac_base_ver > 10:
    AS_TARGET_NAME = "Music"
else:
    AS_TARGET_NAME = "iTunes"

################################################################################
# applescript helpers
################################################################################
def _make(ascript, wrap=True):
    if wrap: ascript = _wrap(ascript)
    return applescript.AppleScript(source=ascript)

#-------------------------------------------------------------------------------
def _wrap(ascript):
    return '''
    on run(args)
        tell application "{}"
    		with timeout of 6 seconds
            	{}
        	end timeout
        end tell
    end run
    '''.format(AS_TARGET_NAME, ascript)

#-------------------------------------------------------------------------------
def _run(script_object, *args):
    if len(args) == 1 and isinstance(args[0], (list,tuple,indigo.List)):
        args = list(args[0])
    try:
        return script_object.run(*args)
    except Exception as e:
        indigo.server.log(f"Applescript runtime error", isError=True)
        indigo.server.log(f"Applescript: {inspect.stack()[1][3]}, args: {args}", isError=True)
        indigo.server.log(str(e), isError=True)

################################################################################
# create all the applescript objects
################################################################################
_launch = _make('''
        activate
    ''')

#-------------------------------------------------------------------------------
_quit = _make('''
        quit
    ''')

#-------------------------------------------------------------------------------
_running = _make('''
        return application "{}" is running
    '''.format(AS_TARGET_NAME), wrap=False)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_volume_get = _make('''
        return sound volume
    ''')

#-------------------------------------------------------------------------------
_volume_set = _make('''
        set sound volume to (item 1 of args)
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_playpause = _make('''
        playpause
    ''')

#-------------------------------------------------------------------------------
_play = _make('''
        play
    ''')

#-------------------------------------------------------------------------------
_pause = _make('''
        pause
    ''')

#-------------------------------------------------------------------------------
_stop = _make('''
        stop
    ''')

#-------------------------------------------------------------------------------
_next = _make('''
        next track
    ''')

#-------------------------------------------------------------------------------
_prev = _make('''
        previous track
    ''')

#-------------------------------------------------------------------------------
_back = _make('''
        back track
    ''')

#-------------------------------------------------------------------------------
_player_state_get = _make('''
        return player state as string
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_playlist_play = _make('''
        play playlist named (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
_playlists = _make('''
    	return (get name of every playlist where special kind is none)
    ''')

#-------------------------------------------------------------------------------
_playlist_current = _make('''
    	try
    		set current_playlist to name of current playlist
    	on error
    		set current_playlist to "None"
    	end try
        return current_playlist
    ''')

###-------------------------------------------------------------------------------
_album_get = _make('''
        try
        	if (album of the current track is not missing value) then
        		get album of the current track
        	end if	
        end try
    ''')

###-------------------------------------------------------------------------------
_artist_get = _make('''
        try
        	if (artist of the current track is not missing value) then
        		get artist of the current track
        	end if	
        end try
    ''')

###-------------------------------------------------------------------------------
_track_get = _make('''
        try
        	if (name of the current track is not missing value) then
        		get name of the current track
        	end if	
        end try
    ''')

#-------------------------------------------------------------------------------
_stream_title = _make('''
    	try
    		set stream_title to current stream title
    	on error
    		set stream_title to "None"
    	end try
        return stream_title
    ''')

#-------------------------------------------------------------------------------
_track_duration_get = _make('''
        try
        	if (duration of the current track is not missing value) then
        		get duration of the current track
        	end if	
        end try
    ''')

_player_pos_get = _make('''
        try
        	if (player position is not missing value) then
        		get player position
        	end if
        end try
    ''')

_player_pos_set = _make('''
        try
        	if (player state is playing) or (player state is paused) then
        		set player position to (item 1 of args)
        	end if
        end try
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_play_single_track = _make('''
        -- get track to be played
    	set input_playlist to playlist named (item 1 of args)
    	if (item 2 of args) is missing value then
    		set track_id to (random number from 1 to (count tracks in input_playlist))
    	else
    		set track_id to (item 2 of args)
    	end if
    	set the_track to track track_id of input_playlist

        -- prep the playlist
    	set single_playlist_name to "Indigo Single Track"        
    	try
    		set single_playlist to user playlist single_playlist_name
    		delete every track of single_playlist
    	on error
    		set single_playlist to make new playlist with properties {name:single_playlist_name}
    	end try

        -- add track to playlist
    	duplicate the_track to single_playlist

        -- play track via playlist
    	play single_playlist
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_shuffle_state_get = _make('''
    	return shuffle enabled
    ''')

#-------------------------------------------------------------------------------
_shuffle_state_set = _make('''
    	set shuffle enabled to (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
_shuffle_mode_get = _make('''
    	return shuffle mode as string
    ''')

#-------------------------------------------------------------------------------
_shuffle_mode_set = _make('''
    	if (item 1 of args) is "songs" then
    		set shuffle mode to songs
    	else if (item 1 of args) is "albums" then
    		set shuffle mode to albums
    	else if (item 1 of args) is "groupings" then
    		set shuffle mode to groupings
        else
            error
    	end if
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_repeat_get = _make('''
    	return song repeat as string
    ''')

#-------------------------------------------------------------------------------
_repeat_set = _make('''
    	if (item 1 of args) is "off" then
    		set song repeat to off
    	else if (item 1 of args) is "one" then
    		set song repeat to one
    	else if (item 1 of args) is "all" then
    		set song repeat to all
        else
            error
    	end if
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_eq_state_get = _make('''
    	return EQ enabled
    ''')

#-------------------------------------------------------------------------------
_eq_state_set = _make('''
    	set EQ enabled to (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
_eq_presets = _make('''
    	return (get name of every EQ preset)
    ''')

#-------------------------------------------------------------------------------
_eq_preset_get = _make('''
    	return name of current EQ preset as string
    ''')

#-------------------------------------------------------------------------------
_eq_preset_set = _make('''
    	set current EQ preset to EQ preset named (item 1 of args)
    ''')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
_airplay_devices_all = _make('''
    	return (get name of every AirPlay device)
    ''')

#-------------------------------------------------------------------------------
_airplay_devices_active_get = _make('''
        return (get name of every AirPlay device whose selected is true)
    ''')

#-------------------------------------------------------------------------------
_airplay_devices_active_set = _make('''
        set airplay_list to {}
        repeat with device_name in args
            set end of airplay_list to (AirPlay device device_name)
        end repeat
        set current AirPlay devices to airplay_list
    ''')

#-------------------------------------------------------------------------------
_airplay_device_active_get = _make('''
        return selected of AirPlay device named (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
_airplay_device_active_set = _make('''
        set selected of AirPlay device named (item 1 of args) to (item 2 of args)
    ''')

#-------------------------------------------------------------------------------
_airplay_device_volume_get = _make('''
        return sound volume of AirPlay device named (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
_airplay_device_volume_set = _make('''
        set sound volume of AirPlay device named (item 1 of args) to (item 2 of args)
    ''')

################################################################################
# callable methods
################################################################################
def launch():
    return _run(_launch)

#-------------------------------------------------------------------------------
def quit():
    return _run(_quit)

#-------------------------------------------------------------------------------
def running():
    return _run(_running)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def volume_get():
    return _run(_volume_get)

#-------------------------------------------------------------------------------
def volume_set(volume):
    return _run(_volume_set, volume)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def playpause():
    return _run(_playpause)

#-------------------------------------------------------------------------------
def play():
    return _run(_play)

#-------------------------------------------------------------------------------
def pause():
    return _run(_pause)

#-------------------------------------------------------------------------------
def stop():
    return _run(_stop)

#-------------------------------------------------------------------------------
def next():
    return _run(_next)

#-------------------------------------------------------------------------------
def prev():
    return _run(_prev)

#-------------------------------------------------------------------------------
def back():
    return _run(_back)

#-------------------------------------------------------------------------------
def player_state_get():
    return _run(_player_state_get)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def playlist_play(playlist):
    return _run(_playlist_play, playlist)

#-------------------------------------------------------------------------------
def playlists():
    return _run(_playlists)

#-------------------------------------------------------------------------------
def playlist_current():
    return _run(_playlist_current)

#-------------------------------------------------------------------------------
def stream_title():
    return _run(_stream_title)

###-------------------------------------------------------------------------------
def album_get():
    return _run(_album_get)

###-------------------------------------------------------------------------------
def artist_get():
    return _run(_artist_get)

###-------------------------------------------------------------------------------
def track_get():
    return _run(_track_get)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def track_duration_get():
    return _run(_track_duration_get)

def player_pos_get():
    return _run(_player_pos_get)

def player_pos_set(player_pos):
    return _run(_player_pos_set, player_pos)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def play_single_track(playlist, trackId):
    if trackId is None:
        trackId = applescript.kMissingValue
    return _run(_play_single_track, playlist, trackId)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def shuffle_state_get():
    return _run(_shuffle_state_get)

#-------------------------------------------------------------------------------
def shuffle_state_set(shuffle):
    return _run(_shuffle_state_set, shuffle)

#-------------------------------------------------------------------------------
def shuffle_mode_get():
    return _run(_shuffle_mode_get)

#-------------------------------------------------------------------------------
def shuffle_mode_set(shuffle):
    return _run(_shuffle_mode_set, shuffle.lower())

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def repeat_get():
    return _run(_repeat_get)

#-------------------------------------------------------------------------------
def repeat_set(repeat):
    return _run(_repeat_set, repeat.lower())

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def eq_state_get():
    return _run(_eq_state_get)

#-------------------------------------------------------------------------------
def eq_state_set(eq):
    return _run(_eq_state_set, eq)

#-------------------------------------------------------------------------------
def eq_presets():
    return _run(_eq_presets)

#-------------------------------------------------------------------------------
def eq_preset_get():
    return _run(_eq_preset_get)

#-------------------------------------------------------------------------------
def eq_preset_set(preset):
    return _run(_eq_preset_set, preset)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def airplay_devices_all():
    return _run(_airplay_devices_all)

#-------------------------------------------------------------------------------
def airplay_devices_active_get():
    return _run(_airplay_devices_active_get)

#-------------------------------------------------------------------------------
def airplay_devices_active_set(airplayDeviceList):
    return _run(_airplay_devices_active_set, airplayDeviceList)

#-------------------------------------------------------------------------------
def airplay_device_active_get(airplayDevice):
    return _run(_airplay_device_active_get, airplayDevice)

#-------------------------------------------------------------------------------
def airplay_device_active_set(airplayDevice, airplayStatus):
    return _run(_airplay_device_active_set, airplayDevice, airplayStatus)

#-------------------------------------------------------------------------------
def airplay_device_volume_get(airplayDevice):
    return _run(_airplay_device_volume_get, airplayDevice)

#-------------------------------------------------------------------------------
def airplay_device_volume_set(airplayDevice, airplayVolume):
    return _run(_airplay_device_volume_set, airplayDevice, airplayVolume)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def playApplescriptSpecifier(specifier):
    return executeApplescriptText('''play {}'''.format(specifier))

#-------------------------------------------------------------------------------
def executeApplescriptText(appleScriptText):
    applescriptObject = _make(appleScriptText)
    return _run(applescriptObject)
