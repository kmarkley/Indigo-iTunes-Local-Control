#! /usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
# iTunes Applescripts
################################################################################

import applescript

################################################################################
# make all the applescript objects
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
        set sound volume to arg
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
        play playlist arg
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
    	set shuffle enabled to arg
    ''')

#-------------------------------------------------------------------------------
_shuffle_mode_get = _make('''
    	return shuffle mode
    ''')

#-------------------------------------------------------------------------------
_shuffle_mode_set = _make('''
    	set shuffle mode to arg
    ''')

#-------------------------------------------------------------------------------
_repeat_get = _make('''
    	return song repeat
    ''')

#-------------------------------------------------------------------------------
_repeat_set = _make('''
    	set song repeat to arg
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
        set current AirPlay devices to arg
    ''')

#-------------------------------------------------------------------------------
_airplay_device_active_get = _make('''
        return selected of AirPlay device arg
    ''')

#-------------------------------------------------------------------------------
_airplay_device_active_set = _make('''
        set device_name to item 1 of arg
        set device_active to item 2 of arg
        set selected of AirPlay device device_name to device_active
    ''')

#-------------------------------------------------------------------------------
_airplay_device_volume_get = _make('''
        return sound volume of AirPlay device arg
    ''')

#-------------------------------------------------------------------------------
_airplay_device_volume_set = _make('''
        set device_name to item 1 of arg
        set device_volume to item 2 of arg
        set sound volume of AirPlay device device_name to device_volume
    ''')

################################################################################
#
################################################################################
def launch():
    return _launch.run(None)

#-------------------------------------------------------------------------------
def quit():
    return _quit.run(None)

#-------------------------------------------------------------------------------
def running():
    return _running.run(None)

#-------------------------------------------------------------------------------
def volume_get():
    return _volume_get.run(None)

#-------------------------------------------------------------------------------
def volume_set(volume):
    return _volume_set.run(volume)

#-------------------------------------------------------------------------------
def playpause():
    return _playpause.run(None)

#-------------------------------------------------------------------------------
def play():
    return _play.run(None)

#-------------------------------------------------------------------------------
def pause():
    return _pause.run(None)

#-------------------------------------------------------------------------------
def stop():
    return _stop.run(None)

#-------------------------------------------------------------------------------
def next():
    return _next.run(None)

#-------------------------------------------------------------------------------
def prev():
    return _prev.run(None)

#-------------------------------------------------------------------------------
def back():
    return _back.run(None)

#-------------------------------------------------------------------------------
def playlist_play(playlist):
    return _playlist_play.run(playlist)

#-------------------------------------------------------------------------------
def playlists():
    return _playlists.run(None)

#-------------------------------------------------------------------------------
def playlist_current():
    return _playlist_current.run(None)

#-------------------------------------------------------------------------------
def shuffle_state_get():
    return _shuffle_state_get.run(None)

#-------------------------------------------------------------------------------
def shuffle_state_set(shuffle):
    return _shuffle_state_set.run(shuffle)

#-------------------------------------------------------------------------------
def shuffle_mode_get():
    return _shuffle_mode_get.run(None)

#-------------------------------------------------------------------------------
def shuffle_mode_set(shuffle):
    return _shuffle_mode_set.run(shuffle)

#-------------------------------------------------------------------------------
def repeat_get():
    return _repeat_get.run(None)

#-------------------------------------------------------------------------------
def repeat_set(repeat):
    return _repeat_set.run(repeat)

#-------------------------------------------------------------------------------
def airplay_devices_all():
    return _airplay_devices_all.run(None)

#-------------------------------------------------------------------------------
def airplay_devices_active_get():
    return _airplay_devices_active_get.run(None)

#-------------------------------------------------------------------------------
def airplay_devices_active_set(airplayDeviceList):
    airplayList = ['AirPlay device "{}"'.format(item) for item in airplayDeviceList]
    return _airplay_devices_active_set.run(airplayList)

#-------------------------------------------------------------------------------
def airplay_device_active_get(airplayDevice):
    return _airplay_device_active_get.run(airplayDevice)

#-------------------------------------------------------------------------------
def airplay_device_active_set(airplayDevice, airplayStatus):
    return _airplay_device_active_set.run((airplayDevice, airplayStatus))

#-------------------------------------------------------------------------------
def airplay_device_volume_get(airplayDevice):
    return _airplay_device_volume_get.run(airplayDevice)

#-------------------------------------------------------------------------------
def airplay_device_volume_set(airplayDevice, airplayVolume):
    return _airplay_device_volume_set.run((airplayDevice, airplayVolume))

################################################################################
# Applescript helpers
################################################################################
def _make(ascript, wrap=True):
    if wrap: ascript = _wrap(ascript)
    return applescript.AppleScript(source=ascript)

#-------------------------------------------------------------------------------
def _wrap(ascript):
    return '''
    on run(arg)
        tell application "iTunes"
            {}
        end tell
    end run
    '''.format(ascript)
