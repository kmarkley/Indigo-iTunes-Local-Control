#! /usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
# iTunes Applescripts
################################################################################

import applescript
import indigo
import inspect

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
        tell application "iTunes"
            {}
        end tell
    end run
    '''.format(ascript)

#-------------------------------------------------------------------------------
def _run(script_object, *args):
    if len(args) == 1 and isinstance(args[0], (list,tuple,indigo.List)):
        args = list(args[0])
    try:
        return script_object.run(*args)
    except:
        indigo.server.log('applescript:{}, args:{}'.format(inspect.stack()[1][3],args), isError=True)

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
        return application "iTunes" is running
    ''', wrap=False)

#-------------------------------------------------------------------------------
_volume_get = _make('''
        return sound volume
    ''')

#-------------------------------------------------------------------------------
_volume_set = _make('''
        set sound volume to (item 1 of args)
    ''')

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
def volume_get():
    return _run(_volume_get)

#-------------------------------------------------------------------------------
def volume_set(volume):
    return _run(_volume_set, volume)

#-------------------------------------------------------------------------------
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
def playlist_play(playlist):
    return _run(_playlist_play, playlist)

#-------------------------------------------------------------------------------
def playlists():
    return _run(_playlists)

#-------------------------------------------------------------------------------
def playlist_current():
    return _run(_playlist_current)

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
def repeat_get():
    return _run(_repeat_get)

#-------------------------------------------------------------------------------
def repeat_set(repeat):
    return _run(_repeat_set, repeat.lower())

#-------------------------------------------------------------------------------
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
