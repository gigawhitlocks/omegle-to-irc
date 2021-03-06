import cleverbot
import irc.bot
from time import sleep
from random import random, randrange

class CleverBot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        irc.bot.SingleServerIRCBot.__init__(self, [("irc.freenode.net", 6667)], "Clomegle", "Clomegle")
        self.bot = cleverbot.Session()
        self.omeglenick = "omegle-stranger"
        self.autoreply = True
        self.channel = "#omegle-cleverbot"


    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        msg = e.arguments[0].encode("ascii", "ignore")
        if msg == "manual":
            c.privmsg(e.source.split("!")[0], "Set to manual")
            self.autoreply = False
        elif msg == "auto":
            c.privmsg(e.source.split("!")[0], "Set to auto")
            self.autoreply = True

    def on_pubmsg(self, c, e):
        if self.autoreply:
            arg = e.arguments[0].encode("ascii", "ignore")
            if (e.source.split("!")[0] == self.omeglenick):
                if (arg != "<stranger connected>" and arg != "<stranger disconnected>"):
                    if (arg == "myyy caaaammm goot so daark on heeere buut looooks ok at my blooogg"):
                        c.privmsg(self.omeglenick, "disconnect")
                    else:
                        reply = self.bot.Ask(arg).lower()
                        while (len(reply) == 0):
                            reply = self.bot.Ask(Arg).lower()

                        if reply[-1] == '.':
                            reply = reply[:-1]
                        if (len(reply) > 35):
                            sleep(((len(reply) / 35) - 1))
                        c.privmsg(self.channel, self.omeglenick + ": " + reply)


bot = CleverBot()
bot.start()
