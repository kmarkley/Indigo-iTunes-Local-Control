#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo
import threading
import time
from ast import literal_eval as literal
import iTunesAppleScript as itunes

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

################################################################################
# globals


################################################################################
class Plugin(indigo.PluginBase):

    #-------------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.control = Control()
        self.fade = Fade(0,0.0,True)
        self.airplay = Airplay()

    #-------------------------------------------------------------------------------
    def __del__(self):
        indigo.PluginBase.__del__(self)

    #-------------------------------------------------------------------------------
    # Start and Stop
    #-------------------------------------------------------------------------------
    def startup(self):
        self.debug = self.pluginPrefs.get('showDebugInfo',False)
        if self.debug:
            self.logger.debug("Debug logging enabled")

    #-------------------------------------------------------------------------------
    def shutdown(self):
        self.pluginPrefs['showDebugInfo'] = self.debug

    #-------------------------------------------------------------------------------
    # Config and Validate
    #-------------------------------------------------------------------------------
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo',False)
            self.logger.debug("Debug logging {}".format(["disabled","enabled"][self.debug]))

    #-------------------------------------------------------------------------------
    def validatePrefsConfigUi(self, valuesDict):
        errorsDict = indigo.Dict()

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    #-------------------------------------------------------------------------------
    def validateActionConfigUi(self, valuesDict, typeId, devId):
        errorsDict = indigo.Dict()

        if not valuesDict.get('volume','1').isdigit():
            errorsDict['volume'] = "Must be a positive integer"
        elif not (0 <= int(valuesDict.get('volume','1')) <= 100):
            errorsDict['volume'] = "Must be between 0 and 100"

        if not valuesDict.get('duration','1').isdigit():
            errorsDict['duration'] = "Must be a positive integer"

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    #-------------------------------------------------------------------------------
    # Action Methods
    #-------------------------------------------------------------------------------
    def launch(self, action):
        self.onState = True

    #-------------------------------------------------------------------------------
    def quit(self, action):
        self.onState = False

    #-------------------------------------------------------------------------------
    def toggle(self, action):
        self.onState = not self.onState

    #-------------------------------------------------------------------------------
    def setVolume(self, action):
        self.volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def increaseVolume(self, action):
        self.volume += int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def decreaseVolume(self, action):
        self.volume -= int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def volumeToVariable(self, action):
        variable_set(action.props['variable'],self.volume)

    #-------------------------------------------------------------------------------
    def volumeFromVariable(self, action):
        self.volume = variable_get(action.props['variable'],int)

    #-------------------------------------------------------------------------------
    def fadeVolumeTo(self, action):
        self.fadeStart(action.props['volume'], action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeUp(self, action):
        self.fadeStart(self.volume + int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeDown(self, action):
        self.fadeStart(self.volume - int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeFromVariable(self, action):
        self.fadeStart(variable_get(action.props['variable'],int), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeStart(self, volume, duration):
        self.fade.cancel()
        self.fade = Fade(volume, duration)

    #-------------------------------------------------------------------------------
    def fadeStop(self, action):
        self.fade.cancel()

    #-------------------------------------------------------------------------------
    def play(self, action):
        self.control.play()

    #-------------------------------------------------------------------------------
    def pause(self, action):
        self.control.pause()

    #-------------------------------------------------------------------------------
    def playpause(self, action):
        self.control.playpause()

    #-------------------------------------------------------------------------------
    def stop(self, action):
        self.control.stop()

    #-------------------------------------------------------------------------------
    def next(self, action):
        self.control.next()

    #-------------------------------------------------------------------------------
    def prev(self, action):
        self.control.prev()

    #-------------------------------------------------------------------------------
    def back(self, action):
        self.control.back()

    #-------------------------------------------------------------------------------
    def playPlaylist(self, action):
        self.playlist = action.props['playlist']

    #-------------------------------------------------------------------------------
    def playlistToVariable(self, action):
        variable_set(action.props['variable'],self.playlist)

    #-------------------------------------------------------------------------------
    def playlistFromVariable(self, action):
        self.playlist = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def shuffleStateOn(self, action):
        self.shuffleState = True

    #-------------------------------------------------------------------------------
    def shuffleStateOff(self, action):
        self.shuffleState = False

    #-------------------------------------------------------------------------------
    def shuffleStateToggle(self, action):
        self.shuffleState = not self.shuffleState

    #-------------------------------------------------------------------------------
    def shuffleStateToVariable(self, action):
        variable_set(action.props['variable'],self.shuffleState)

    #-------------------------------------------------------------------------------
    def shuffleStateFromVariable(self, action):
        self.shuffleState = variable_get(action.props['variable'],bool)

    #-------------------------------------------------------------------------------
    def shuffleModeSongs(self, action):
        self.shuffleMode = 'songs'

    #-------------------------------------------------------------------------------
    def shuffleModeAlbums(self, action):
        self.shuffleMode = 'albums'

    #-------------------------------------------------------------------------------
    def shuffleModeGroupings(self, action):
        self.shuffleMode = 'groupings'

    #-------------------------------------------------------------------------------
    def shuffleModeToVariable(self, action):
        variable_set(action.props['variable'],self.shuffleMode)

    #-------------------------------------------------------------------------------
    def shuffleModeFromVariable(self, action):
        self.shuffleMode = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def repeatSet(self, action):
        self.repeat = action.props['repeat']

    #-------------------------------------------------------------------------------
    def repeatOff(self, action):
        self.repeat = 'off'

    #-------------------------------------------------------------------------------
    def repeatOne(self, action):
        self.repeat = 'one'

    #-------------------------------------------------------------------------------
    def repeatAll(self, action):
        self.repeat = 'all'

    #-------------------------------------------------------------------------------
    def repeatToVariable(self, action):
        variable_set(action.props['variable'],self.repeat)

    #-------------------------------------------------------------------------------
    def repeatFromVariable(self, action):
        self.repeat = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def airplayDeviceStatus(self, action):
        self.airplay.device(action.props['device']).active = action.props['status']
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDeviceAdd(self, action):
        self.airplay.device(action.props['device']).active = True

    #-------------------------------------------------------------------------------
    def airplayDeviceRemove(self, action):
        self.airplay.device(action.props['device']).active = False

    #-------------------------------------------------------------------------------
    def airplayDeviceToggle(self, action):
        self.airplay.device(action.props['device']).toggle()

    #-------------------------------------------------------------------------------
    def airplayDeviceVolume(self, action):
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDevicesGroup(self, action):
        self.airplay.active_devices = action.props['devices']

    #-------------------------------------------------------------------------------
    def airplayDevicesToVariable(self, action):
        devices = self.airplay.active_devices
        if action.props['convert']:
            devices = ', '.join(devices)
        variable_set(action.props['variable'],devices)

    #-------------------------------------------------------------------------------
    def airplayDevicesFromVariable(self, action):
        self.airplay.active_devices = variable_get(action.props['variable'], list)

    #-------------------------------------------------------------------------------
    # Menu Methods
    #-------------------------------------------------------------------------------
    def toggleDebug(self):
        if self.debug:
            self.logger.debug("Debug logging disabled")
            self.debug = False
        else:
            self.debug = True
            self.logger.debug("Debug logging enabled")

    #-------------------------------------------------------------------------------
    # Menu Callbacks
    #-------------------------------------------------------------------------------
    def menu_airplay_devices(self, filter='', valuesDict=dict(), typeId='', targetId=0):
        return [(item,item) for item in self.airplay.all_devices]

    #-------------------------------------------------------------------------------
    def menu_playlists(self, filter='', valuesDict=dict(), typeId='', targetId=0):
        return [(item,item) for item in self.playlists]

    #-------------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------------
    def _onStateGet(self):
        return itunes.running()
    def _onStateSet(self, value):
        if value:
            itunes.launch()
        else:
            itunes.quit()
    onState = property(_onStateGet,_onStateSet)

    #-------------------------------------------------------------------------------
    def _volumeGet(self):
        return itunes.volume_get()
    def _volumeSet(self, value):
        self.fade.cancel()
        itunes.volume_set(normalize_volume(value))
    volume = property(_volumeGet,_volumeSet)

    #-------------------------------------------------------------------------------
    def _shuffleStateGet(self):
        return itunes.shuffle_state_get()
    def _shuffleStateSet(self, value):
        itunes.shuffle_state_set(value)
    shuffleState = property(_shuffleStateGet,_shuffleStateSet)

    #-------------------------------------------------------------------------------
    def _shuffleModeGet(self):
        return itunes.shuffle_mode_get()
    def _shuffleModeSet(self, value):
        itunes.shuffle_mode_set(value)
    shuffleMode = property(_shuffleModeGet,_shuffleModeSet)

    #-------------------------------------------------------------------------------
    def _repeatGet(self):
        return itunes.repeat_get()
    def _repeatSet(self, value):
        itunes.repeat_set(value)
    repeat = property(_repeatGet,_repeatSet)

    #-------------------------------------------------------------------------------
    def itunes.playlistGet(self):
        return itunes.playlist_current()
    def itunes.playlistSet(self,value):
        if value != self.playlist:
            itunes.playlist_play(value)
    playlist = property(itunes.playlistGet,itunes.playlistSet)

    #-------------------------------------------------------------------------------
    @property
    def playlists(self):
        return itunes.playlists()

################################################################################
# Classes
################################################################################
class Control(object):

    #-------------------------------------------------------------------------------
    def play(self):
        itunes.play()

    #-------------------------------------------------------------------------------
    def pause(self):
        itunes.pause()

    #-------------------------------------------------------------------------------
    def playpause(self):
        itunes.playpause()

    #-------------------------------------------------------------------------------
    def stop(self):
        itunes.stop()

    #-------------------------------------------------------------------------------
    def next(self):
        itunes.next()

    #-------------------------------------------------------------------------------
    def prev(self):
        itunes.prev()

    #-------------------------------------------------------------------------------
    def back(self):
        itunes.back()

################################################################################
class Fade(threading.Thread):

    k_min_step = 0.2
    k_max_loop = 0.1

    #-------------------------------------------------------------------------------
    def __init__(self, volume, duration, dummy=False):
        super(Fade, self).__init__()
        self.daemon     = True
        self.cancelled  = False

        self.start_volume = itunes.volume_get()
        self.end_volume = normalize_volume(volume)
        self.step_size = [-1,1][self.end_volume >= self.start_volume]
        self.step_count = abs(self.end_volume - self.start_volume)
        self.fade_duration = float(duration)

        if dummy:
            # placeholder instance
            self.cancelled = True
        elif self.step_count == 0:
            # no volume change
            self.cancelled = True
        elif self.fade_duration <= self.k_min_step:
            # instant volume change
            itunes.volume_set(self.end_volume)
            self.cancelled = True
        else:
            # actual fade
            self.step_wait = self.fade_duration/self.step_count
            while self.step_wait < self.k_min_step:
                # ensure minimum time between steps
                self.step_wait = self.step_wait * 2
                self.step_size = self.step_size * 2
                self.step_count = int(self.fade_duration/self.step_wait)

            self.final = (self.start_volume + self.step_count * self.step_size != self.end_volume)

            self.loop_wait = self.step_wait
            while self.loop_wait > self.k_max_loop:
                # loop on multiple of step_wait
                self.loop_wait = self.loop_wait / 2

            # do the fade
            self.start()

    #-------------------------------------------------------------------------------
    def run(self):
        next_step = time.time() + self.step_wait
        volume = self.start_volume
        count = 0
        while (not self.cancelled) and (count != self.step_count):
            loop_time = time.time()
            if loop_time >= next_step:
                volume += self.step_size
                count += 1
                itunes.volume_set(volume)
                next_step = loop_time + self.step_wait
            time.sleep(max(0, self.loop_wait - (time.time() - loop_time)))
        if (not self.cancelled) and self.final:
            itunes.volume_set(self.end_volume)

    #-------------------------------------------------------------------------------
    def cancel(self):
        self.cancelled = True
        while self.isAlive():
            time.sleep(self.k_max_loop)

################################################################################
class Airplay(object):

    #-------------------------------------------------------------------------------
    def __init__(self):
        self.devices = dict()
        nada = self.all_devices

    #-------------------------------------------------------------------------------
    def _getActive(self):
        return itunes.airplay_devices_active_get()
    def _setActive(self,deviceList):
        itunes.airplay_devices_active_set(deviceList)
    active_devices = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    @property
    def all_devices(self):
        return itunes.airplay_devices_all()

    #-------------------------------------------------------------------------------
    def device(self,name):
        return AirplayDevice(name)

################################################################################
class AirplayDevice(object):

    #-------------------------------------------------------------------------------
    def __init__(self,name):
        self.name = name

    #-------------------------------------------------------------------------------
    def _getActive(self):
        return itunes.airplay_device_active_get(self.name)
    def _setActive(self,value):
        itunes.airplay_device_active_set(self.name,value)
    active = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    def toggle(self):
        self.active = not self.active

    #-------------------------------------------------------------------------------
    def _getVolume(self):
        itunes.airplay_device_volume_get(self.name)
    def _setVolume(self,volume):
        volume = normalize_volume(volume)/100.0 * itunes.volume_get()
        itunes.airplay_device_volume_set(self.name, normalize_volume(volume))
    volume = property(_getVolume,_setVolume)

################################################################################
# Utilitites
################################################################################
def zint(value):
    try: return int(value)
    except: return 0

#-------------------------------------------------------------------------------
def normalize_volume(value):
    volume = zint(value)
    if volume > 100:
        return 100
    elif volume < 0:
        return 0
    else:
        return volume

#-------------------------------------------------------------------------------
def variable_get(varId,type=str):
    if type in (bool, int, float, str):
        return indigo.variables[int(varId)].getValue(type)
    else:
        return literal(indigo.variables[int(varId)].value)

#-------------------------------------------------------------------------------
def variable_set(varId,value):
    indigo.variable.updateValue(int(varId),unicode(value))
