import functools

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc

from omegletwist import OmegleBot
import random


def trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print( "%s(%s %s)" % (func.__name__, args, kwargs))
        return func(*args, **kwargs)
    return wrapper


bridge_bot_dispatch = {}  # eg {'command': command_func}

def generate_nickname():
#    adjectives = open("adjectives.txt","r").readlines()
#    nouns = open("nouns.txt","r").readlines()
#    return random.choice(adjectives).strip()+random.choice(["_","-"])+random.choice(nouns).strip()
    return "omegle-stranger"

def command(f):
    @functools.wraps(f)
    def command_wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    bridge_bot_dispatch["%s" % f.__name__] = f

class BridgeBotProtocol(irc.IRCClient):
    """An irc bot that bridges to Omegle conversations."""

    # attributes set in factory:
    #   active_nickname
    #   idle_nickname
    #   omegle_bot

    dontspeak = False
    idle = False  # hack to force idle on init connect
    piping_user = None
    first_message = True
    controller = None 
    autoconnect = True
    lines = 1

    @command
    def connect(self, *args):
        """Get a stranger to talk to."""
        d = self.omegle_bot.connect()

        def after_connect(connect_info):
            self.goActive()

        d.addCallback(after_connect)

    @command
    def disconnect(self, *args):
        """Disconnect from our current stranger."""
        self.omegle_bot.disconnect()
        self.goIdle()

    @command
    def help(self, *args):
        self.msg(self.controller, 'Possible commands:')
        for cmd_name in sorted(bridge_bot_dispatch.keys()):
            self.msg(self.controller, "  %s" % cmd_name)

    @command
    def captcha(self, *args):
        self.omegle_bot.solveCaptcha(' '.join(args))

    @command
    def pipe(self, *args):
        if len(args) > 0:
            self.piping_user = args[0]
            print ("Piping to %r." % self.piping_user)
            self.first_message = True
            self.msg(self.controller, "<piping to %r>" % self.piping_user)
        else:
            self.msg(self.controller, 'Usage: pipe <nick>')

    @command
    def unpipe(self, *args):
        self.msg(self.controller, "<no longer piping to %r>" % self.piping_user)
        self.piping_user = None

    @command
    def popcorn(self, *args):
        self.msg(self.controller, '<will auto-reconnect>')
        self.autoconnect = True
    
    @command
    def unpopcorn(self, *args):
        self.msg(self.controller, '<will not auto-reconnect>')
        self.autoconnect = False

    def goIdle(self):
        if not self.idle:
            self.idle = True

    def goActive(self):
        if self.idle:
            self.idle = False

    def signedOn(self):
        self.join(self.factory.channel)
        print( "Signed on as %s." % (self.nickname,))

    def joined(self, channel):
        print ("Joined %s." % (channel,))
        self.goIdle()

    def privmsg(self, user, channel, msg):
        user = user.split('!')[0]
        # if the target is talking & bot isnt idle

        if channel == self.nickname: 
        # the controller directed a msg at us; need to respond
            print ("<- '%s' (%s)" % (msg, user))

            msg_split = msg.split()
            command_name, args = msg_split[0], msg_split[1:]

            command = bridge_bot_dispatch.get(command_name)
            if command:
                command(self, *args)

            elif not self.idle:
                print ('bot:', msg)
                #self.omegle_bot.say(self.piping_user + ": " + msg)
                self.omegle_bot.say(self.piping_user + ": " + msg)

        if user != self.nickname and msg == "<stranger disconnected>":
            self.dontspeak = True
            self.omegle_bot.disconnect()
            self.goIdle()

        if not self.idle:
            if self.nickname in msg:
                msg = msg.split(" ")
                newmsg = []
                for m in msg:
                    if self.nickname not in m:
                        newmsg.append(m)
                msg = (" ").join(newmsg)
                print(msg) 
                self.omegle_bot.say(msg)
                return

    def typingCallback(self, *args):
        pass

    def stoppedTypingCallback(self, *args):
        pass

    def disconnectCallback(self, *args):
        print ('disconnected')
        if not self.dontspeak:
            self.say(self.factory.channel, '<stranger disconnected>')

        if self.autoconnect:
            bridge_bot_dispatch['connect'](self)
        else:
            self.goIdle()

    def messageCallback(self, *args):
        msg = args[1][0].encode('utf-8')
        print ('stranger:', msg)

        if self.piping_user:
            msg = self.piping_user + ': ' + msg

        self.say(self.factory.channel, msg)



    @trace
    def recaptchaFailedCallback(self, *args):
        self.msg(self.controller, '<captcha was incorrect>')

    @trace
    def recaptchaRequiredCallback(self, *args):
        msg = ("<Omegle requires a captcha."
               " Solve it using `captcha <solutiontext>`."
               " url: %s") % args[1]

        self.msg(self.controller, msg)

    def connectCallback(self, *args):
        print ('connected')
        self.dontspeak = False
        self.say(self.factory.channel, '<stranger connected>')
        self.goActive()

    def waitingCallback(self, *args):
        pass


import sys
class BridgeBotFactory(protocol.ClientFactory):
    protocol = BridgeBotProtocol
    def __init__(self, channel):
        self.channel = channel
        self.nickname = generate_nickname()
        self.controller = sys.argv[1] 

    def buildProtocol(self, *args, **kw):
        prot = protocol.ClientFactory.buildProtocol(self, *args, **kw)
        prot.nickname = self.nickname
        prot.controller = self.controller
        prot.active_nickname = prot.nickname
        prot.idle_nickname = prot.nickname
        prot.omegle_bot = OmegleBot(prot)

        return prot

    def clientConnectionLost(self, connector, reason):
        print ("Lost connection (%s), reconnecting." % (reason,))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print ("Could not connect: %s" % (reason,))


if __name__ == '__main__':
    if len(sys.argv) == 5:
        reactor.connectTCP(sys.argv[2],
                           int(sys.argv[3]),
                           BridgeBotFactory(sys.argv[4]),
                          )
    else:
        for x in sys.argv:
            print(x)
        print("Got "+str(len(sys.argv))+" arguments.\nUsage: python2 bridge.py <controller_nick> <server> <port> #<room>")
        sys.exit()

    reactor.run()
