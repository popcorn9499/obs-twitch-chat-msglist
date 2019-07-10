import obspython as obs
import time
import asyncio
import threading
import irc
import os
from utils import config
import streamList

source_name = ""

# ------------------------------------------------------------


def refresh_pressed(props, prop): #refreshes the msg list
    """
    Called when the 'refresh' button defined below is pressed
    """
    print("Refresh Pressed")
    config.streamList = streamList.streamList()

def connect_pressed(props, prop): #connect button to start the entire asyncio event loop
    config.stopThread = False
    config.secondaryThread  = main()
    config.secondaryThread.start()

def disconnect_pressed(props, prop): #disconnect button to stop the entire asyncio event loop
    config.stopThread = True
    print("closed")
    time.sleep(0.1)

def update_text(text): #updates 
    global source_name
    source = obs.obs_get_source_by_name(source_name)
    if source is not None:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

# ------------------------------------------------------------


def script_properties():
    """
    Called to define user properties associated with the script. These
    properties are used to define how to show settings properties to a user.
    """
    props = obs.obs_properties_create()

    obs.obs_properties_add_text(props,"IRC Server","IRC Server",obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props,"IRC Channel","IRC Channel",obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props,"IRC Port","Port",0,65535,1)
    obs.obs_properties_add_text(props,"IRC Nickname","Nickname",obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props,"IRC Password","Password",obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_button(props, "button1", "Connect", connect_pressed)
    obs.obs_properties_add_button(props, "button2", "Disconnect", disconnect_pressed)
    p = obs.obs_properties_add_list(props, "source", "Text Source",
                                    obs.OBS_COMBO_TYPE_EDITABLE,
                                    obs.OBS_COMBO_FORMAT_STRING)
    obs.obs_properties_add_text(props,"Command Prefix","Command Prefix",obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_button(props, "button", "Refresh Msg List", refresh_pressed)


    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)
    return props


def script_update(settings):
    """
    Called when the script’s settings (if any) have been changed by the user.
    """
    global source_name

    source_name = obs.obs_data_get_string(settings, "source")
    ircServer = obs.obs_data_get_string(settings, "IRC Server")
    ircChannel = obs.obs_data_get_string(settings, "IRC Channel")
    ircPort = obs.obs_data_get_int(settings, "IRC Port")
    ircNickname = obs.obs_data_get_string(settings, "IRC Nickname")
    ircPassword = obs.obs_data_get_string(settings, "IRC Password")
    config.commandPrefix = obs.obs_data_get_string(settings, "Command Prefix")
    config.irc = {
        "Enabled": True,
        "Servers": {
            ircServer:{
                "Channel":{
                    ircChannel:{
                        "Enabled": True
                    }
                },
                "Enabled": True,
                "Nickname": ircNickname,
                "Password": ircPassword,
                "Port": ircPort
            }
        }
    }
    config.obsSource = source_name

def displayNextHotkey(pressed):
    if pressed:
        text = config.streamList.displayNext()
        update_text(text)

def displayPrevHotkey(pressed):
    if pressed:
        text = config.streamList.displayPrev()
        update_text(text)
    

# A function named script_load will be called on startup
def script_load(settings):
    config.streamList = streamList.streamList()
    #streamMsgDispNext
    config.dispNext_hotkey_id = obs.obs_hotkey_register_frontend("streamMsgDispNext", "Stream Msg Increment", displayNextHotkey)
    hotkey_save_array = obs.obs_data_get_array(settings, "streamMsgDispNext")
    obs.obs_hotkey_load(config.dispNext_hotkey_id, hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
    #streamMsgDispPrev
    config.dispPrev_hotkey_id = obs.obs_hotkey_register_frontend("streamMsgDispPrev", "Stream Msg Decrement", displayPrevHotkey)
    hotkey_save_array = obs.obs_data_get_array(settings, "streamMsgDispPrev")
    obs.obs_hotkey_load(config.dispPrev_hotkey_id, hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)

    #loads all the initial configs from obs for the tool
    source_name = obs.obs_data_get_string(settings, "source")
    ircServer = obs.obs_data_get_string(settings, "IRC Server")
    ircChannel = obs.obs_data_get_string(settings, "IRC Channel")
    ircPort = obs.obs_data_get_int(settings, "IRC Port")
    ircNickname = obs.obs_data_get_string(settings, "IRC Nickname")
    ircPassword = obs.obs_data_get_string(settings, "IRC Password")
    config.commandPrefix = obs.obs_data_get_string(settings, "Command Prefix")
    config.irc = {
        "Enabled": True,
        "Servers": {
            ircServer:{
                "Channel":{
                    ircChannel:{
                        "Enabled": True
                    }
                },
                "Enabled": True,
                "Nickname": ircNickname,
                "Password": ircPassword,
                "Port": ircPort
            }
        }
    }
    config.obsSource = source_name

    config.secondaryThread = main()
    config.secondaryThread.start()
    

# A function named script_save will be called when the script is saved
#
# NOTE: This function is usually used for saving extra data (such as in this
# case, a hotkey's save data).  Settings set via the properties are saved
# automatically.
def script_save(settings):
    #streamMsgDispNext
    hotkey_save_array = obs.obs_hotkey_save(config.dispNext_hotkey_id)
    obs.obs_data_set_array(settings, "streamMsgDispNext", hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
    #streamMsgDispPrev
    hotkey_save_array = obs.obs_hotkey_save(config.dispPrev_hotkey_id)
    obs.obs_data_set_array(settings, "streamMsgDispPrev", hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)

def script_unload():
    config.stopThread = True
    print("closed")
    time.sleep(0.1)
    obs.obs_hotkey_unregister(displayNextHotkey)
    obs.obs_hotkey_unregister(displayPrevHotkey)


#################################
#my code
class main(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.loop = asyncio.new_event_loop() #creates a brand new async loop in the new thread

    async def threadOpen(self): #loops constantly to determine if we should close the asyncio loop and therefore close the thread open
        print("Checking")
        while True:
            if config.stopThread:
                await config.ircObj.quitIRC()
                self.loop.stop()
                print("Client stopped")
            await asyncio.sleep(1)

    def run(self):
        irc.ircStart(self.loop)

        try:
            self.loop.run_until_complete(self.threadOpen())
        except RuntimeError:
            print("THREAD DEAD")
        self.loop.close()
        print("Closing")


config.stopThread = False


