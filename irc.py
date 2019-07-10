import asyncio
import re

from utils import config
from utils import logger
import os
import time

##this is the event loop for the irc client
class irc():#alot of this code was given to me from thehiddengamer then i adapted to more of what i needed
    def __init__(self):
        self.messagepattern = re.compile(r"^:(.{1,50})!")
        self.l = logger.logs("IRC")
        self.l.logger.info("Starting")
        self.serviceStarted = {}
        for sKey, sVal in config.irc["Servers"].items():
            if sVal["Enabled"] == True:
                self.serviceStarted.update({sKey:False})
        self.writer = {}
        self.reader = {}

        self.msgHandlerTasks = {}
    
    async def irc_bot(self, loop): #this all works, well, except for when both SweetieBot and SweetieBot_ are used. -- prints will be removed once finished, likely.        
        for sKey, sVal in config.irc["Servers"].items():
            if sVal["Enabled"] == True:
                host = sKey
                print(type(host))
                self.l.logger.info("{0} - Connecting".format(host))
                loop.create_task(self.ircConnect(loop,host))
            else:
                await asyncio.sleep(3)
        try:#stops the crash if no irc settings r set
            self.l.logger.info("Connected: " + host)#wtf is this ment for anymore?
        except UnboundLocalError:
            pass
    
    async def quitIRC(self):
        for key,val in self.writer.items():
            val.write('QUIT Bye \r\n'.encode("utf-8"))
        await asyncio.sleep(20)

    async def ircConnect(self,loop,host):#handles the irc connection
        while True:
            try:
                self.readerBasic, self.writerBasic = await asyncio.open_connection(host,config.irc["Servers"][host]["Port"], loop=loop)
                self.reader.update({host: self.readerBasic})
                self.writer.update({host: self.writerBasic})
                self.l.logger.debug("{0} - Reader {1} ".format(host,self.reader))
                self.l.logger.debug("{0} - Writer {1} ".format(host, self.writer))
                await asyncio.sleep(3)
                if config.irc["Servers"][host]["Password"] != "":
                    self.writer[host].write(b'PASS ' + config.irc["Servers"][host]["Password"].encode('utf-8') + b'\r\n')
                    self.l.logger.info("{0} - Inputing password ".format(host)) #,"Info")
                self.l.logger.info("{0} - Setting user {1}+ ".format(host,config.irc["Servers"][host]["Nickname"]))
                self.writer[host].write(b'NICK ' + config.irc["Servers"][host]["Nickname"].encode('utf-8') + b'\r\n')
                self.l.logger.info("{0} - Setting user {1}".format(host,config.irc["Servers"][host]["Nickname"]))
                self.writer[host].write(b'USER ' + config.irc["Servers"][host]["Nickname"].encode('utf-8') + b' B hi :' + config.irc["Servers"][host]["Nickname"].encode('utf-8') + b'\r\n')
                await asyncio.sleep(3)
                self.l.logger.info("{0} - Joining channels".format(host))
                for key, val in config.irc["Servers"][host]["Channel"].items():
                    if val["Enabled"] == True:
                        print(key)
                        self.writer[host].write(b'JOIN ' + key.encode('utf-8')+ b'\r\n')
                        self.l.logger.info("{0} - Joining channel {1}".format(host,key))
                await asyncio.sleep(3)
                self.l.logger.info("{0} - Initiating IRC Reader".format(host))
                self.msgHandlerTasks.update({host: loop.create_task(self.handleMsg(loop,host))})
                self.serviceStarted[host] = True 
                while not self.msgHandlerTasks[host].done():
                    await asyncio.sleep(5)
            except Exception as e:
                self.l.logger.info(e)
            await asyncio.sleep(10) #retry timeout
        


    async def keepAlive(self,loop,host):
        while True:
            try:
                self.writer[host].write("PING {0} ".format(host).encode("utf-8") + b'\r\n')
            except ConnectionResetError:
                self.msgHandlerTasks[host].cancel() #kills the handler task to recreate the entire connection again
                await self.ircConnect(loop,host)
                break
            except asyncio.streams.IncompleteReadError:
                pass
            await asyncio.sleep(60)
                   
       
            
    async def handleMsg(self,loop,host):
        #info_pattern = re.compile(r'00[1234]|37[526]|CAP')
        await asyncio.sleep(1)
        loop.create_task(self.keepAlive(loop,host)) #creates the keep alive task
        while True:
            if host in self.reader:
                try:
                    data = (await self.reader[host].readuntil(b'\n')).decode("utf-8")
                    data = data.rstrip()
                    data = data.split()
                    self.l.logger.debug(' '.join(data) + host) #,"Extra Debug")
                    if data[0].startswith('@'): 
                        data.pop(0)
                    if data == []:
                        pass
                    elif data[0] == 'PING':
                        print(data)
                        self.writer[host].write(b'PONG %s\r\n' % data[1].encode("utf-8"))
                    # elif data[0] == ':user1.irc.popicraft.net' or data[0] ==':irc.popicraft.net' or info_pattern.match(data[1]):
                        # print('[Twitch] ', ' '.join(data))
                        #generally not-as-important info
                    else:
                        print(data)
                        await self._decoded_send(data, loop,host)
                except ConnectionResetError:
                    #self.ircConnect(loop,host)
                    break
                except asyncio.streams.IncompleteReadError:
                    pass
            else:
                print("{0} doesnt exist".format(host))        
    
    async def _decoded_send(self, data, loop,host):
        """TODO: remove discord only features..."""
        
        if data[1] == 'PRIVMSG':
            user = data[0].split('!')[0].lstrip(":")
            m = re.search(self.messagepattern, data[0])
            #meCheck = config.c.irc["Servers"][host]["Nickname"] == user
            if m: #and not meCheck:
                message = ' '.join(data[3:]).strip(':').split()
                self.l.logger.info("{0} - ".format(host) + data[2]+ ":" + user +': '+ ' '.join(message))
                msgStats = {"sentFrom":"IRC","msgData": None,"Bot":"IRC","Server": host,"Channel": data[2], "author": user,"authorData": None,"authorsRole": {"Normal": 0},"msg":' '.join(message),"sent":False}
                role = {}
                role.update({"Normal": 0})
                await config.streamList.addList(message)

        elif data[1] == 'JOIN':
            user = data[0].split('!')[0].lstrip(":")
            self.l.logger.info("{0} - ".format(host)  + user+" joined")
            msgStats = {"sentFrom":"IRC","msgData": None,"Bot":"IRC","Server": host,"Channel": data[2], "author": user,"authorData": None,"authorsRole": {"Normal": 0},"msg":"{0} joined the channel".format(user),"sent":False}
        elif data[1] == 'PART' or data[1] == 'QUIT':
            user = data[0].split('!')[0].lstrip(":")
            self.l.logger.info("{0} - ".format(host) + user+" left")
            msgStats = {"sentFrom":"IRC","msgData": None,"Bot":"IRC","Server": host,"Channel": data[2], "author": user,"authorData": None,"authorsRole": {"Normal": 0},"msg":"{0} left the channel ({1})".format(user,data[3]),"sent":False}
        elif data[1] == 'NOTICE':
            pass
        elif data[1] == 'KICK':
            self.l.logger.info("{0} - ".format(host) + "I was kicked")
            self.writer[host].write('QUIT Bye \r\n'.encode("utf-8"))
            await asyncio.sleep(10)
            await self.ircConnect(loop,host)
            loop.stop()
        elif data[1] == 'RECONNECT':
            self.l.logger.info("{0} - ".format(host) + "Reconnecting")
            self.writer[host].write('QUIT Bye \r\n'.encode("utf-8"))
            await asyncio.sleep(10)
            await self.ircConnect(loop,host)
            loop.stop()

        elif data[0] == "ERROR":
            if ' '.join([data[1],data[2]]) == ":Closing link:":
                self.writer[host].write('QUIT Bye \r\n'.encode("utf-8"))
                #print("[Twitch] Lost Connection or disconnected: %s" % ' '.join(data[4:]))
                self.l.logger.info("{0} - ".format(host) + "Lost connection")
                await asyncio.sleep(10)
                await self.ircConnect(loop,host)
                loop.stop()
        
#this starts everything for the irc client 
##possibly could of put all this in a class and been done with it?
def ircStart(loop):
    IRC = irc()
    config.ircObj = IRC
    if config.irc["Enabled"] == True:
        loop.create_task(IRC.irc_bot(loop))
        print("started")
    print("Heyo")
