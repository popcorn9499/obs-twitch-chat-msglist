import asyncio
from utils import config
import threading
import obspython as obs

class streamList():
    def __init__(self):
        self.msgList = []
        self.curPos = -1

    async def addList(self,message):
        if (message[0] == "!add"):
            print("Adding " + message[1])
            message.pop(0)
            self.msgList.append(" ".join(message))
            if self.curPos == -1:
                await self.updateSource()

    def displayNext(self):
        print("Displaying next")
        if len(self.msgList) > self.curPos + 1:
            self.curPos += 1
            return self.msgList[self.curPos]
        elif self.curPos == -1:
            return ""
        else:
            return self.msgList[self.curPos]

    def displayPrev(self):
        print("Displaying Prev")
        if self.curPos > 0:
            self.curPos -= 1
            return self.msgList[self.curPos]
        elif self.curPos == -1:
            return ""
        else:
            return self.msgList[self.curPos]

    async def updateSource(self):
        source = obs.obs_get_source_by_name(config.obsSource)
        text = config.streamList.displayNext()
        if source is not None:
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text)
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)