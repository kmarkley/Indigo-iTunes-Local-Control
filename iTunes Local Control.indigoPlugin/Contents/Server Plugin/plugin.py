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
import iTunesAppleScript as itunes

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

################################################################################
# globals

MIN_STEP_TIME = 0.2
MAX_LOOP_TIME = 0.05

################################################################################
class Plugin(indigo.PluginBase):

    #-------------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

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
        global MIN_STEP_TIME
        MIN_STEP_TIME = self.pluginPrefs.get('minStepTime',0.2)

        self.control = Control(self)
        self.airplay = Airplay(self)
        self.fader   = Fader(self)

    #-------------------------------------------------------------------------------
    def shutdown(self):
        self.pluginPrefs['showDebugInfo'] = self.debug
        self.pluginPrefs['minStepTime'] = MIN_STEP_TIME
        self.fader.cancel()

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

        positiveIntegerFields = ['duration', 'trackNumber']
        otherRequiredFields = ['variable','playlist','trackName','device','status','specifier','applescriptText']

        for key, value in valuesDict.items():
            if key == 'volume':
                if not validateTextFieldNumber(value, numberType=int, zeroAllowed=True, negativeAllowed=False, maximumAllowed=100):
                    errorsDict[key] = "Must be an integer between 0 and 100"
            elif key in positiveIntegerFields:
                if not validateTextFieldNumber(value, numberType=int, zeroAllowed=False, negativeAllowed=False):
                    errorsDict[key] = "Must be a positive integer"
            elif key in otherRequiredFields:
                if value == "":
                    errorsDict[key] = "Required"

        if len(errorsDict) > 0:
            self.logger.debug(u'\n{}'.format(valuesDict))
            return (False, valuesDict, errorsDict)
        else:
            return (True, valuesDict)

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Action Methods
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def launch(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.onState = True

    #-------------------------------------------------------------------------------
    def quit(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.onState = False

    #-------------------------------------------------------------------------------
    def toggle(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.onState = not self.onState

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def play(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.play()

    #-------------------------------------------------------------------------------
    def pause(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.pause()

    #-------------------------------------------------------------------------------
    def playpause(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.playpause()

    #-------------------------------------------------------------------------------
    def stop(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.stop()

    #-------------------------------------------------------------------------------
    def next(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.next()

    #-------------------------------------------------------------------------------
    def prev(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.prev()

    #-------------------------------------------------------------------------------
    def back(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.control.back()

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def setVolume(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['volume']))
        self.volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def increaseVolume(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['volume']))
        self.volume += int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def decreaseVolume(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['volume']))
        self.volume -= int(action.props['volume'])

    #-------------------------------------------------------------------------------
    def volumeToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.volume)

    #-------------------------------------------------------------------------------
    def volumeFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.volume = variable_get(action.props['variable'],int)

    #-------------------------------------------------------------------------------
    def fadeVolumeTo(self, action):
        self.logger.debug(u'action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(action.props['volume'], action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeUp(self, action):
        self.logger.debug(u'action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(self.volume + int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeVolumeDown(self, action):
        self.logger.debug(u'action "{}": {}/{}s'.format(action.description,action.props['volume'],action.props['duration']))
        self.fadeStart(self.volume - int(action.props['volume']), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.fadeStart(variable_get(action.props['variable'],int), action.props['duration'])

    #-------------------------------------------------------------------------------
    def fadeStart(self, volume, duration):
        self.fader.fade(volume, duration)

    #-------------------------------------------------------------------------------
    def fadeStop(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.fader.stop()

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def playPlaylist(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['playlist']))
        self.shuffle_state = False
        self.playlist = action.props['playlist']

    #-------------------------------------------------------------------------------
    def playPlaylistShuffled(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['playlist']))
        self.shuffle_mode = 'songs'
        self.shuffle_state = True
        self.playlist = action.props['playlist']

    #-------------------------------------------------------------------------------
    def playlistToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.playlist)

    #-------------------------------------------------------------------------------
    def playlistFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.playlist = variable_get(action.props['variable'])

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def playSingleTrackPlaylistNumber(self, action):
        self.logger.debug(u'action "{}": {} {}'.format(action.description, action.props['playlist'], int(action.props['trackNumber'])))
        itunes.play_single_track(action.props['playlist'], int(action.props['trackNumber']))

    #-------------------------------------------------------------------------------
    def playSingleTrackPlaylistName(self, action):
        self.logger.debug(u'action "{}": {} {}'.format(action.description, action.props['playlist'], action.props['trackName']))
        itunes.play_single_track(action.props['playlist'], action.props['trackName'])

    #-------------------------------------------------------------------------------
    def playSingleTrackPlaylistRandom(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description, action.props['playlist']))
        itunes.play_single_track(action.props['playlist'], None)

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def shuffleStateOn(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_state = True

    #-------------------------------------------------------------------------------
    def shuffleStateOff(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_state = False

    #-------------------------------------------------------------------------------
    def shuffleStateToggle(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_state = not self.shuffle_state

    #-------------------------------------------------------------------------------
    def shuffleStateToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.shuffle_state)

    #-------------------------------------------------------------------------------
    def shuffleStateFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.shuffle_state = variable_get(action.props['variable'],bool)

    #-------------------------------------------------------------------------------
    def shuffleModeSongs(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_mode = 'songs'

    #-------------------------------------------------------------------------------
    def shuffleModeAlbums(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_mode = 'albums'

    #-------------------------------------------------------------------------------
    def shuffleModeGroupings(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.shuffle_mode = 'groupings'

    #-------------------------------------------------------------------------------
    def shuffleModeToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.shuffle_mode)

    #-------------------------------------------------------------------------------
    def shuffleModeFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.shuffle_mode = variable_get(action.props['variable'])

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def repeatOff(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.repeat = 'off'

    #-------------------------------------------------------------------------------
    def repeatOne(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.repeat = 'one'

    #-------------------------------------------------------------------------------
    def repeatAll(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.repeat = 'all'

    #-------------------------------------------------------------------------------
    def repeatToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.repeat)

    #-------------------------------------------------------------------------------
    def repeatFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.repeat = variable_get(action.props['variable'])

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def eqStateOn(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.eq_state = True

    #-------------------------------------------------------------------------------
    def eqStateOff(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.eq_state = False

    #-------------------------------------------------------------------------------
    def eqStateToggle(self, action):
        self.logger.debug(u'action "{}"'.format(action.description))
        self.eq_state = not self.eq_state

    #-------------------------------------------------------------------------------
    def eqStateToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.eq_state)

    #-------------------------------------------------------------------------------
    def eqStateFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.eq_state = variable_get(action.props['variable'],bool)

    #-------------------------------------------------------------------------------
    def eqPresetSet(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['preset']))
        self.eq_preset = action.props['preset']

    #-------------------------------------------------------------------------------
    def eqPresetToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.eq_preset)

    #-------------------------------------------------------------------------------
    def eqPresetFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.eq_preset = variable_get(action.props['variable'])

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def airplayDeviceStatus(self, action):
        self.logger.debug(u'action "{}": {}@{} {}'.format(action.description,action.props['device'],action.props['volume'],action.props['status']))
        self.airplay.device(action.props['device']).active = action.props['status']
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDeviceAdd(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).active = True

    #-------------------------------------------------------------------------------
    def airplayDeviceRemove(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).active = False

    #-------------------------------------------------------------------------------
    def airplayDeviceToggle(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['device']))
        self.airplay.device(action.props['device']).toggle()

    #-------------------------------------------------------------------------------
    def airplayDeviceVolume(self, action):
        self.logger.debug(u'action "{}": {}@{}'.format(action.description,action.props['device'],action.props['volume']))
        self.airplay.device(action.props['device']).volume = action.props['volume']

    #-------------------------------------------------------------------------------
    def airplayDevicesGroup(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,list(action.props['devices'])))
        self.airplay.active_devices = action.props['devices']

    #-------------------------------------------------------------------------------
    def airplayDevicesToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        devices = self.airplay.active_devices
        if action.props['convert']:
            devices = ', '.join(devices)
        variable_set(action.props['variable'],devices)

    #-------------------------------------------------------------------------------
    def airplayDevicesFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.airplay.active_devices = variable_get(action.props['variable'], list)

    #-------------------------------------------------------------------------------
    def currentSettingsToVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        variable_set(action.props['variable'],self.settings)

    #-------------------------------------------------------------------------------
    def currentSettingsFromVariable(self, action):
        self.logger.debug(u'action "{}": {}'.format(action.description,action.props['variable']))
        self.settings = variable_get(action.props['variable'], dict)

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def playApplescriptSpecifier(self, action):
        itunes.playApplescriptSpecifier(action.props['specifier'])

    #-------------------------------------------------------------------------------
    def executeApplescriptText(self, action):
        itunes.executeApplescriptText(action.props['applescriptText'])

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
    def menu_eq_presets(self, filter='', valuesDict=dict(), typeId='', targetId=0):
        return [(item,item) for item in self.eq_presets]

    #-------------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------------
    def _onState_get(self):
        value = itunes.running()
        self.logger.debug(u'get running: {}'.format(value))
        return value
    def _onState_set(self, value):
        self.logger.debug(u'set running: {}'.format(value))
        if value:
            itunes.launch()
        else:
            itunes.quit()
    onState = property(_onState_get,_onState_set)

    #-------------------------------------------------------------------------------
    def _volume_get(self):
        value = itunes.volume_get()
        self.logger.debug(u'get volume: {}'.format(value))
        return value
    def _volume_set(self, value):
        value = normalize_volume(value)
        self.fader.stop()
        self.logger.debug(u'set volume: {}'.format(value))
        itunes.volume_set(value)
    volume = property(_volume_get,_volume_set)

    #-------------------------------------------------------------------------------
    @property
    def playlists(self):
        value = itunes.playlists()
        self.logger.debug(u'all playlists: {}'.format(value))
        return value

    #-------------------------------------------------------------------------------
    def _playlist_get(self):
        value = itunes.playlist_current()
        self.logger.debug(u'get playlist: {}'.format(value))
        return value
    def _playlist_set(self,value):
        self.logger.debug(u'set playlist: {}'.format(value))
        itunes.playlist_play(value)
    playlist = property(_playlist_get,_playlist_set)

    #-------------------------------------------------------------------------------
    def _shuffle_state_get(self):
        value = itunes.shuffle_state_get()
        self.logger.debug(u'get shuffle state: {}'.format(value))
        return value
    def _shuffle_state_set(self, value):
        self.logger.debug(u'set shuffle state: {}'.format(value))
        itunes.shuffle_state_set(value)
    shuffle_state = property(_shuffle_state_get,_shuffle_state_set)

    #-------------------------------------------------------------------------------
    def _shuffle_mode_get(self):
        value = itunes.shuffle_mode_get()
        self.logger.debug(u'get shuffle mode: {}'.format(value))
        return value
    def _shuffle_mode_set(self, value):
        self.logger.debug(u'set shuffle mode: {}'.format(value))
        itunes.shuffle_mode_set(value)
    shuffle_mode = property(_shuffle_mode_get,_shuffle_mode_set)

    #-------------------------------------------------------------------------------
    def _repeat_get(self):
        value = itunes.repeat_get()
        self.logger.debug(u'get repeat: {}'.format(value))
        return value
    def _repeat_set(self, value):
        self.logger.debug(u'set repeat: {}'.format(value))
        itunes.repeat_set(value)
    repeat = property(_repeat_get,_repeat_set)

    #-------------------------------------------------------------------------------
    def _eq_state_get(self):
        value = itunes.eq_state_get()
        self.logger.debug(u'get eq state: {}'.format(value))
        return value
    def _eq_state_set(self, value):
        self.logger.debug(u'set eq state: {}'.format(value))
        itunes.eq_state_set(value)
    eq_state = property(_eq_state_get,_eq_state_set)

    #-------------------------------------------------------------------------------
    @property
    def eq_presets(self):
        value = itunes.eq_presets()
        self.logger.debug(u'all eq presets: {}'.format(value))
        return value

    #-------------------------------------------------------------------------------
    def _eq_preset_get(self):
        value = itunes.eq_preset_get()
        self.logger.debug(u'get eq preset: {}'.format(value))
        return value
    def _eq_preset_set(self, value):
        self.logger.debug(u'set eq preset: {}'.format(value))
        itunes.eq_preset_set(value)
    eq_preset = property(_eq_preset_get,_eq_preset_set)

    #-------------------------------------------------------------------------------
    @property
    def player_state(self):
        value = itunes.player_state_get()
        self.logger.debug(u'get player state: {}'.format(value))
        return value

    #-------------------------------------------------------------------------------
    def _settings_get(self):
        active_devices = self.airplay.active_devices
        airplay_volume = dict()
        for deviceName in active_devices:
            airplay_volume[deviceName] = self.airplay.device(deviceName).volume
        settings = {
            'volume':         self.volume,
            'playlist':       self.playlist,
            'shuffle_state':  self.shuffle_state,
            'shuffle_mode':   self.shuffle_mode,
            'repeat':         self.repeat,
            'eq_state':       self.eq_state,
            'eq_preset':      self.eq_preset,
            'player_state':   self.player_state,
            'active_devices': active_devices,
            'airplay_volume': airplay_volume
            }
        return settings
    def _settings_set(self,settings):
        self.volume        = settings['volume']
        self.shuffle_state = settings['shuffle_state']
        self.shuffle_mode  = settings['shuffle_mode']
        self.repeat        = settings['repeat']
        self.eq_state      = settings['eq_state']
        self.eq_preset     = settings['eq_preset']
        self.airplay.active_devices = settings['active_devices']
        for name, volume in settings['airplay_volume'].items():
            if settings['volume'] == 0:
                self.airplay.device(name).volume = 0
            else:
                self.airplay.device(name).volume = int(round(volume*100.0/settings['volume']))
        if settings['playlist'] in self.playlists:
            if settings['player_state'] in ['playing','paused']:
                itunes.playlist_play(settings['playlist'])
            if settings['player_state'] == 'paused':
                itunes.pause()
    settings = property(_settings_get,_settings_set)

################################################################################
# Classes
################################################################################
class Control(object):

    #-------------------------------------------------------------------------------
    def __init__(self, plugin):
        self.logger = plugin.logger

    #-------------------------------------------------------------------------------
    def play(self):
        self.logger.debug(u'control: play')
        itunes.play()

    #-------------------------------------------------------------------------------
    def pause(self):
        self.logger.debug(u'control: pause')
        itunes.pause()

    #-------------------------------------------------------------------------------
    def playpause(self):
        self.logger.debug(u'control: playpause')
        itunes.playpause()

    #-------------------------------------------------------------------------------
    def stop(self):
        self.logger.debug(u'control: stop')
        itunes.stop()

    #-------------------------------------------------------------------------------
    def next(self):
        self.logger.debug(u'control: next')
        itunes.next()

    #-------------------------------------------------------------------------------
    def prev(self):
        self.logger.debug(u'control: prev')
        itunes.prev()

    #-------------------------------------------------------------------------------
    def back(self):
        self.logger.debug(u'control: back')
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
            self.logger.debug(u'no fade: no volume change')
        elif duration <= MIN_STEP_TIME:
            # instant volume change
            self.logger.debug(u'no fade: instant volume change')
            itunes.volume_set(end_volume)
        else:
            # actual fade

            # calculate fade steps
            step_size = up_down = [-1,1][end_volume >= start_volume]
            step_wait = duration/step_count
            while step_wait < MIN_STEP_TIME:
                # ensure minimumAllowed time between steps
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
            self.logger.debug(u'start fade: v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(end_volume,duration,step_count,step_size,step_wait))

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
                self.logger.debug(u'end fade:   v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(volume,time.time()-time_start,count,step_size,step_wait))
            else:
                self.logger.debug(u'stop fade:  v{}/{:.4f}s ({}/{:+}/{:.4f})'.format(volume,time.time()-time_start,count,step_size,step_wait))

    #-------------------------------------------------------------------------------
    def run(self):
        self.logger.debug(u'Fader thread started')
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
            self.logger.debug(u'Fader thread cancelled')

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
        self.logger.debug(u'get active airplay devices: {}'.format(list(value)))
        return value
    def _setActive(self,value):
        self.logger.debug(u'set active airplay devices: {}'.format(list(value)))
        itunes.airplay_devices_active_set(value)
    active_devices = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    @property
    def all_devices(self):
        value = itunes.airplay_devices_all()
        self.logger.debug(u'get all airplay devices: {}'.format(value))
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
        self.logger.debug(u'get airplay "{}" status: {}'.format(self.name,value))
        return value
    def _setActive(self,value):
        self.logger.debug(u'set airplay "{}" status: {}'.format(self.name,value))
        itunes.airplay_device_active_set(self.name,value)
    active = property(_getActive,_setActive)

    #-------------------------------------------------------------------------------
    def toggle(self):
        self.active = not self.active

    #-------------------------------------------------------------------------------
    def _getVolume(self):
        value = itunes.airplay_device_volume_get(self.name)
        self.logger.debug(u'get airplay "{}" volume: {}'.format(self.name,value))
        return value
    def _setVolume(self,value):
        value = int(normalize_volume(value)/100.0 * itunes.volume_get())
        self.logger.debug(u'set airplay "{}" volume: {}'.format(self.name,value))
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

#-------------------------------------------------------------------------------
def validateTextFieldNumber(rawInput, numberType=float, zeroAllowed=True, negativeAllowed=True, minimumAllowed=None, maximumAllowed=None):
    try:
        num = numberType(rawInput)
        if not zeroAllowed:
            if num == 0: raise
        if not negativeAllowed:
            if num < 0: raise
        if minimumAllowed is not None:
            if num < minimumAllowed: raise
        if maximumAllowed is not None:
            if num > maximumAllowed: raise
        return True
    except:
        return False
