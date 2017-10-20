#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo
import time
import threading
import Queue
from ast import literal_eval as literal
from ghpu import GitHubPluginUpdater
import iTunesAppleScript as itunes

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

################################################################################
# globals

kPluginUpdateCheckHours = 24

MIN_STEP_TIME = 0.2
MAX_LOOP_TIME = 0.05

################################################################################
class Plugin(indigo.PluginBase):

    #-------------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.updater = GitHubPluginUpdater(self)
        self.control = Control(self)
        self.airplay = Airplay(self)
        self.fader   = Fader(self)

    #-------------------------------------------------------------------------------
    def __del__(self):
        indigo.PluginBase.__del__(self)

    #-------------------------------------------------------------------------------
    # Start and Stop
    #-------------------------------------------------------------------------------
    def startup(self):
        self.nextCheck = self.pluginPrefs.get('nextUpdateCheck',0)
        self.debug = self.pluginPrefs.get('showDebugInfo',False)
        if self.debug:
            self.logger.debug("Debug logging enabled")
        global MIN_STEP_TIME
        MIN_STEP_TIME = self.pluginPrefs.get('minStepTime',0.2)

    #-------------------------------------------------------------------------------
    def shutdown(self):
        self.pluginPrefs['nextUpdateCheck'] = self.nextCheck
        self.pluginPrefs['showDebugInfo'] = self.debug
        self.pluginPrefs['minStepTime'] = MIN_STEP_TIME
        self.fader.cancel()

    #-------------------------------------------------------------------------------
    def runConcurrentThread(self):
        try:
            while True:
                if time.time() > self.nextCheck:
                    self.checkForUpdates()
                self.sleep(600)
        except self.StopThread:
            pass    # Optionally catch the StopThread exception and do any needed cleanup.
    #-------------------------------------------------------------------------------
    # Config and Validate
    #-------------------------------------------------------------------------------
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo',False)
            self.logger.debug("Debug logging {}".format(["disabled","enabled"][self.debug]))
            global MIN_STEP_TIME
            MIN_STEP_TIME = self.pluginPrefs.get('minStepTime',0.2)

    #-------------------------------------------------------------------------------
    def validatePrefsConfigUi(self, valuesDict):
        errorsDict = indigo.Dict()

        try:
            valuesDict['minStepTime'] = round(float(valuesDict['minStepTime']),4)
            if not (0.1 <= valuesDict['minStepTime'] <= 1):
                raise ValueError
        except:
            errorsDict['minStepTime'] = 'Must be number between 0.1 and 1.0'

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
        self.logger.debug('action "{}"'.format(action.description))
        self.onState = True

    #-------------------------------------------------------------------------------
    def quit(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.onState = False

    #-------------------------------------------------------------------------------
    def toggle(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.onState = not self.onState

    #-------------------------------------------------------------------------------
    def play(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.play()

    #-------------------------------------------------------------------------------
    def pause(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.pause()

    #-------------------------------------------------------------------------------
    def playpause(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.playpause()

    #-------------------------------------------------------------------------------
    def stop(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.stop()

    #-------------------------------------------------------------------------------
    def next(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.next()

    #-------------------------------------------------------------------------------
    def prev(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.prev()

    #-------------------------------------------------------------------------------
    def back(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.control.back()

    #-------------------------------------------------------------------------------
    def setVolume(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['volume']))
        self.volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def increaseVolume(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['volume']))
        self.volume += int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def decreaseVolume(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['volume']))
        self.volume -= int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def volumeToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.volume)

    #-------------------------------------------------------------------------------
    def volumeFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.volume = variable_get(action.props['variable'],int)

    #-------------------------------------------------------------------------------
    def fadeVolumeTo(self, action):
        self.logger.debug('action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(action.props['volume'], action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeUp(self, action):
        self.logger.debug('action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(self.volume + int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeDown(self, action):
        self.logger.debug('action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(self.volume - int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.fadeStart(variable_get(action.props['variable'],int), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeStart(self, volume, duration):
        self.fader.fade(volume, duration)

    #-------------------------------------------------------------------------------
    def fadeStop(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.fader.stop()

    #-------------------------------------------------------------------------------
    def playPlaylist(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['playlist']))
        self.playlist = action.props['playlist']

    #-------------------------------------------------------------------------------
    def playlistToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.playlist)

    #-------------------------------------------------------------------------------
    def playlistFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.playlist = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def shuffleStateOn(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleState = True

    #-------------------------------------------------------------------------------
    def shuffleStateOff(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleState = False

    #-------------------------------------------------------------------------------
    def shuffleStateToggle(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleState = not self.shuffleState

    #-------------------------------------------------------------------------------
    def shuffleStateToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.shuffleState)

    #-------------------------------------------------------------------------------
    def shuffleStateFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.shuffleState = variable_get(action.props['variable'],bool)

    #-------------------------------------------------------------------------------
    def shuffleModeSongs(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleMode = 'songs'

    #-------------------------------------------------------------------------------
    def shuffleModeAlbums(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleMode = 'albums'

    #-------------------------------------------------------------------------------
    def shuffleModeGroupings(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.shuffleMode = 'groupings'

    #-------------------------------------------------------------------------------
    def shuffleModeToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.shuffleMode)

    #-------------------------------------------------------------------------------
    def shuffleModeFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.shuffleMode = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def repeatOff(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.repeat = 'off'

    #-------------------------------------------------------------------------------
    def repeatOne(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.repeat = 'one'

    #-------------------------------------------------------------------------------
    def repeatAll(self, action):
        self.logger.debug('action "{}"'.format(action.description))
        self.repeat = 'all'

    #-------------------------------------------------------------------------------
    def repeatToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.repeat)

    #-------------------------------------------------------------------------------
    def repeatFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.repeat = variable_get(action.props['variable'])

    #-------------------------------------------------------------------------------
    def airplayDeviceStatus(self, action):
        self.logger.debug('action "{}": {}@{} {}'.format(action.description,action.props['device'],action.props['volume'],action.props['status']))
        self.airplay.device(action.props['device']).active = action.props['status']
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDeviceAdd(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).active = True

    #-------------------------------------------------------------------------------
    def airplayDeviceRemove(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).active = False

    #-------------------------------------------------------------------------------
    def airplayDeviceToggle(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).toggle()

    #-------------------------------------------------------------------------------
    def airplayDeviceVolume(self, action):
        self.logger.debug('action "{}": {}@{}'.format(action.description,action.props['device'],action.props['volume']))
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDevicesGroup(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['devices']))
        self.airplay.active_devices = action.props['devices']

    #-------------------------------------------------------------------------------
    def airplayDevicesToVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        devices = self.airplay.active_devices
        if action.props['convert']:
            devices = ', '.join(devices)
        variable_set(action.props['variable'],devices)

    #-------------------------------------------------------------------------------
    def airplayDevicesFromVariable(self, action):
        self.logger.debug('action "{}": {}'.format(action.description,action.props['variable']))
        self.airplay.active_devices = variable_get(action.props['variable'], list)

    #-------------------------------------------------------------------------------
    # Menu Methods
    #-------------------------------------------------------------------------------
    def checkForUpdates(self):
        self.nextCheck = time.time() + (kPluginUpdateCheckHours*60*60)
        try:
            self.updater.checkForUpdate()
        except Exception as e:
            msg = 'Check for update error.  Next attempt in {} hours.'.format(kPluginUpdateCheckHours)
            if self.debug:
                self.logger.exception(msg)
            else:
                self.logger.error(msg)
                self.logger.debug(e)

    #-------------------------------------------------------------------------------
    def updatePlugin(self):
        self.updater.update()

    #-------------------------------------------------------------------------------
    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

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
        value = itunes.running()
        self.logger.debug('get running: {}'.format(value))
        return value
    def _onStateSet(self, value):
        self.logger.debug('set running: {}'.format(value))
        if value:
            itunes.launch()
        else:
            itunes.quit()
    onState = property(_onStateGet,_onStateSet)

    #-------------------------------------------------------------------------------
    def _volumeGet(self):
        value = itunes.volume_get()
        self.logger.debug('get volume: {}'.format(value))
        return value
    def _volumeSet(self, value):
        value = normalize_volume(value)
        self.fader.stop()
        self.logger.debug('set volume: {}'.format(value))
        itunes.volume_set(value)
    volume = property(_volumeGet,_volumeSet)

    #-------------------------------------------------------------------------------
    def _shuffleStateGet(self):
        value = itunes.shuffle_state_get()
        self.logger.debug('get shuffle: {}'.format(value))
        return value
    def _shuffleStateSet(self, value):
        self.logger.debug('set shuffle: {}'.format(value))
        itunes.shuffle_state_set(value)
    shuffleState = property(_shuffleStateGet,_shuffleStateSet)

    #-------------------------------------------------------------------------------
    def _shuffleModeGet(self):
        value = itunes.shuffle_mode_get()
        self.logger.debug('get mode: {}'.format(value))
        return value
    def _shuffleModeSet(self, value):
        self.logger.debug('set mode: {}'.format(value))
        itunes.shuffle_mode_set(value)
    shuffleMode = property(_shuffleModeGet,_shuffleModeSet)

    #-------------------------------------------------------------------------------
    def _repeatGet(self):
        value = itunes.repeat_get()
        self.logger.debug('get repeat: {}'.format(value))
        return value
    def _repeatSet(self, value):
        self.logger.debug('set repeat: {}'.format(value))
        itunes.repeat_set(value)
    repeat = property(_repeatGet,_repeatSet)

    #-------------------------------------------------------------------------------
    def _playlistGet(self):
        value = itunes.playlist_current()
        self.logger.debug('get playlist: {}'.format(value))
        return value
    def _playlistSet(self,value):
        self.logger.debug('set playlist: {}'.format(value))
        itunes.playlist_play(value)
    playlist = property(_playlistGet,_playlistSet)

    #-------------------------------------------------------------------------------
    @property
    def playlists(self):
        value = itunes.playlists()
        self.logger.debug('all playlists: {}'.format(value))
        return value

################################################################################
# Classes
################################################################################
class Control(object):

    #-------------------------------------------------------------------------------
    def __init__(self, plugin):
        self.logger = plugin.logger

    #-------------------------------------------------------------------------------
    def play(self):
        self.logger.debug('control: play')
        itunes.play()

    #-------------------------------------------------------------------------------
    def pause(self):
        self.logger.debug('control: pause')
        itunes.pause()

    #-------------------------------------------------------------------------------
    def playpause(self):
        self.logger.debug('control: playpause')
        itunes.playpause()

    #-------------------------------------------------------------------------------
    def stop(self):
        self.logger.debug('control: stop')
        itunes.stop()

    #-------------------------------------------------------------------------------
    def next(self):
        self.logger.debug('control: next')
        itunes.next()

    #-------------------------------------------------------------------------------
    def prev(self):
        self.logger.debug('control: prev')
        itunes.prev()

    #-------------------------------------------------------------------------------
    def back(self):
        self.logger.debug('control: back')
        itunes.back()

################################################################################
class Fader(threading.Thread):

    #-------------------------------------------------------------------------------
    def __init__(self, plugin):
        super(Fader, self).__init__()
        self.daemon     = True
        self.cancelled  = False
        self.stopped    = True
        self.queue      = Queue.Queue()
        self.plugin     = plugin
        self.logger     = plugin.logger
        self.start()

    #-------------------------------------------------------------------------------
    def fade(self, volume, duration):
        self.stopped = True
        self.queue.put((volume, duration))

    #-------------------------------------------------------------------------------
    def stop(self):
        self.stopped = True

    #-------------------------------------------------------------------------------
    def _fade(self, volume, duration):
        start_volume = itunes.volume_get()
        end_volume   = normalize_volume(volume)
        step_count   = abs(end_volume - start_volume)
        duration     = float(duration)

        if step_count == 0:
            # no volume change
            self.logger.debug('no fade: no volume change')
        elif duration <= MIN_STEP_TIME:
            # instant volume change
            self.logger.debug('no fade: instance volume change')
            itunes.volume_set(end_volume)
        else:
            # actual fade

            # calculate fade steps
            step_size = up_down = [-1,1][end_volume >= start_volume]
            step_wait = duration/step_count
            while step_wait < MIN_STEP_TIME:
                # ensure minimum time between steps
                step_size += up_down
                step_count = int(abs((end_volume - start_volume)/step_size))
                step_wait = duration/step_count
            final_step = (start_volume + step_count * step_size != end_volume)

            # calculate loop timing
            loop_wait = step_wait
            while loop_wait > MAX_LOOP_TIME:
                # loop on multiple of step_wait
                loop_wait = loop_wait / 2

            # do the fade
            self.stopped = False
            self.logger.debug('start fade: v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(end_volume,duration,step_count,step_size,step_wait))

            time_start = time.time()
            next_step = time_start + step_wait
            volume = start_volume
            count = 0
            while not self.stopped:
                loop_time = time.time()
                if loop_time >= next_step:
                    volume += step_size
                    count += 1
                    itunes.volume_set(volume)
                    next_step += step_wait
                    if count == step_count:
                        break
                time.sleep(max(0, loop_wait - (time.time() - loop_time)))
            if not self.stopped:
                if final_step:
                    volume = end_volume
                    itunes.volume_set(volume)
                self.logger.debug('end fade:   v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(volume,time.time()-time_start,count,step_size,step_wait))
            else:
                self.logger.debug('stop fade:  v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(volume,time.time()-time_start,count,step_size,step_wait))

    #-------------------------------------------------------------------------------
    def run(self):
        self.logger.debug('Fader thread started')
        while not self.cancelled:
            try:
                volume,duration = self.queue.get(True,5)
                self._fade(volume,duration)
            except Queue.Empty:
                pass
            except Exception as e:
                msg = 'Fader thread error \n{}'.format(e)
                if self.plugin.debug:
                    self.logger.exception(msg)
                else:
                    self.logger.error(msg)
        else:
            self.logger.debug('Fader thread cancelled')

    #-------------------------------------------------------------------------------
    def cancel(self):
        self.stopped = True
        self.cancelled = True
        while self.isAlive():
            time.sleep(MAX_LOOP_TIME)

################################################################################
class Airplay(object):

    #-------------------------------------------------------------------------------
    def __init__(self, plugin):
        self.plugin = plugin
        self.logger = plugin.logger

    #-------------------------------------------------------------------------------
    def _getActive(self):
        value = itunes.airplay_devices_active_get()
        self.logger.debug('get active airplay devices: {}'.format(value))
        return value
    def _setActive(self,deviceList):
        self.logger.debug('set active airplay devices: {}'.format(value))
        itunes.airplay_devices_active_set(deviceList)
    active_devices = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    @property
    def all_devices(self):
        value = itunes.airplay_devices_all()
        self.logger.debug('get all airplay devices: {}'.format(value))
        return value

    #-------------------------------------------------------------------------------
    def device(self,name):
        return AirplayDevice(name, self.plugin)

################################################################################
class AirplayDevice(object):

    #-------------------------------------------------------------------------------
    def __init__(self,name,plugin):
        self.name   = name
        self.logger = plugin.logger

    #-------------------------------------------------------------------------------
    def _getActive(self):
        value = itunes.airplay_device_active_get(self.name)
        self.logger.debug('get airplay "{}" status: {}'.format(self.name,value))
        return value
    def _setActive(self,value):
        self.logger.debug('set airplay "{}" status: {}'.format(self.name,value))
        itunes.airplay_device_active_set(self.name,value)
    active = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    def toggle(self):
        self.active = not self.active

    #-------------------------------------------------------------------------------
    def _getVolume(self):
        value = itunes.airplay_device_volume_get(self.name)
        self.logger.debug('get airplay "{}" volume: {}'.format(self.name,value))
        return value
    def _setVolume(self,value):
        value = int(normalize_volume(value)/100.0 * itunes.volume_get())
        self.logger.debug('set airplay "{}" volume: {}'.format(self.name,value))
        itunes.airplay_device_volume_set(self.name, value)
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
