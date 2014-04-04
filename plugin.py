# -*- coding: utf-8 -*-
###
# Copyright (c) 2009-2014, Torrie Fischer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import time
import random

import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sqlite3

class SQLiteMarkovDB(object):
    def __init__(self, filename):
        self.dbs = ircutils.IrcDict()
        self.filename = filename

    def close(self):
        for db in self.dbs.values():
            db.close()

    def _getDb(self, channel):
        if channel not in self.dbs:
            filename = plugins.makeChannelFilename(self.filename, channel)
            self.dbs[channel] = sqlite3.connect(filename)
            c = self.dbs[channel].execute("PRAGMA user_version");
            version = c.fetchone()[0]
            self._upgradeDb(self.dbs[channel], version)
        return self.dbs[channel]

    def _upgradeDb(self, db, current):
        if (current == 0):
            current=1
            db.execute("CREATE TABLE Markov (word TEXT KEY, nextWord TEXT KEY, frequency INTEGER)")
            db.execute("CREATE UNIQUE INDEX wordPair ON Markov (word, nextWord)")
        db.execute("PRAGMA user_version=%i"%current)
        db.commit()

    def addPair(self, channel, first, second):
        c = self._getDb(channel).cursor()
        if (first is None):
            c.execute("SELECT frequency FROM Markov WHERE word IS NULL and nextWord = ?", (second,))
        elif (second is None):
            c.execute("SELECT frequency FROM Markov WHERE word = ? AND nextWord IS NULL", (first,))
        else:
            c.execute("SELECT frequency FROM Markov WHERE word = ? AND nextWord = ?", (first, second))
        res = c.fetchone()
        if (res == None):
            c.execute("INSERT INTO Markov (word, nextWord, frequency) VALUES (?, ?, 0)", (first, second))
            self._getDb(channel).commit()
        if (first is None):
            c.execute("UPDATE Markov SET frequency = frequency+1 WHERE word IS NULL AND nextWord = ?", (second,))
        elif (second is None):
            c.execute("UPDATE Markov SET frequency = frequency+1 WHERE word = ? AND nextWord IS NULL", (first,))
        else:
            c.execute("UPDATE Markov SET frequency = frequency + 1 WHERE word = ? AND nextWord = ?", (first, second))
        self._getDb(channel).commit()

    def nextWord(self, channel, current):
        c = self._getDb(channel).cursor()
        if (current is None):
            c.execute("SELECT nextWord FROM Markov WHERE word IS NULL ORDER BY RANDOM() * frequency LIMIT 1")
        else:
            c.execute("SELECT nextWord FROM Markov WHERE word = ? ORDER BY RANDOM() * frequency LIMIT 1", (current,))
        res = c.fetchone()
        if (res == None):
            return None
        return res[0]

    def close(self):
        for db in self.dbs.itervalues():
            db.commit()
            db.close()

    def buildReply(self, channel, word):
        if (word != None):
            phrase = (word,)
        else:
            phrase = ()
        current = self.nextWord(channel, word)
        while(current != None):
            phrase += (current,)
            current = self.nextWord(channel, current)
        return ' '.join(phrase)

MarkovDB = plugins.DB('ArtificialIntelligence', {'sqlite': SQLiteMarkovDB})

class ArtificialIntelligence(callbacks.Plugin):
    """Add the help for "@plugin help ArtificialIntelligence" here
    This should describe *how* to use this plugin."""
    threaded = False 

    def __init__(self, irc):
        self.__parent = super(ArtificialIntelligence, self)
        super(ArtificialIntelligence, self).__init__(irc)
        self.db = MarkovDB()
        self.lastSpoke = time.time()

    def die(self):
        self.__parent.die()
        self.db.close()

    def tokenize(self, m):
        if ircmsgs.isAction(m):
            return ircmsgs.unAction(m).split()
        elif ircmsgs.isCtcp(m):
            return []
        else:
            return m.args[1].split()

    def doPrivmsg(self, irc, msg):
        if (irc.isChannel(msg.args[0])):
            channel = plugins.getChannel(msg.args[0])
            canSpeak = False
            now = time.time()
            throttle = self.registryValue('randomSpeaking.throttleTime', channel)
            prob = self.registryValue('randomSpeaking.probability', channel)
            delay = self.registryValue('randomSpeaking.maxDelay', channel)
            irc = callbacks.SimpleProxy(irc, msg)
            if now > self.lastSpoke + throttle:
                canSpeak = True
            if canSpeak and random.random() < prob:
                #f = self._markov(channel, irc, prefixNick=False, to=channel, Random=True)
                reply = self.db.buildReply(channel, None)
                if (reply is None):
                    return
                irc.reply(reply, prefixNick=False, to=channel)
                #self._markov(channel, irc, prefixNick=False, to=channel, Random=True)
                #schedule.addEvent(lambda: self.q.enqueue(f), now+delay)
                self.lastSpoke = now+delay
            words = self.tokenize(msg)
            if not words or len(words) == 3:
                return
            if (self.registryValue('ignoreBotCommands', channel) and callbacks.addressed(irc.nick, msg)):
                return
            self.db.addPair(channel, None, words[0])
            self.db.addPair(channel, words[-1], None)
            for (first, second) in utils.seq.window(words, 2):
                self.db.addPair(channel, first, second)

    def _markov(self, channel, irc, word1=None, word2=None, **kwargs):
        minLength = self.registryValue('minChainLength', channel)
        maxTries = self.registryValue('maxAttempts', channel)
        Random = kwargs.pop('Random', None)
        while maxTries > 0:
            maxTries -= 1;
            if word1 and word2:
                givenPair = True
                words = [word1, word2]
            elif word1 or word2:
                givenPair = False
                words = ['\n', word1 or word2]
            else:
                givenPair = False
                try:
                    # words is of the form ['\n', word]
                    words = list(db.getFirstPair(channel))
                except KeyError:
                    irc.error(
                        format('I don\'t have any first pairs for %s.',
                               channel))
                    return # We can't use raise here because the exception
                           # isn't caught and therefore isn't sent to the
                           # server
            follower = words[-1]
            last = False
            resp = []
            while not last:
                resp.append(follower)
                try:
                    (follower,last) = db.getFollower(channel, words[-2],
                                                     words[-1])
                except KeyError:
                    irc.error('I found a broken link in the Markov chain. '
                              ' Maybe I received two bad links to start '
                              'the chain.')
                    return # ditto here re: Raise
                words.append(follower)
            if givenPair:
                if len(words[:-1]) >= minLength:
                    irc.reply(' '.join(words[:-1]), **kwargs)
                    return
                else:
                    continue
            else:
                if len(resp) >= minLength:
                    irc.reply(' '.join(resp), **kwargs)
                    return
                else:
                    continue
        if not Random:
            irc.error(
                format('I was unable to generate a Markov chain at least '
                       '%n long.', (minLength, 'word')))
        else:
            self.log.debug('Not randomSpeaking.  Unable to generate a '
                           'Markov chain at least %n long.',
                           (minLength, 'word'))
        return f
    
    def markov(self, irc, msg, args, channel, word1):
        """[<channel>] [word1]

        Returns a randomly-generated Markov Chain generated sentence from the
        data kept on <channel> (which is only necessary if not sent in the
        channel itself).  If word1 and word2 are specified, they will be used
        to start the Markov chain.
        """
        #f = self._markov(channel, irc, word1, word2,
        #                 prefixNick=False, Random=False)
        #self.q.enqueue(f)
        self.log.debug("%s", word1)
        irc.reply(self.db.buildReply(channel, word1))
    markov = wrap(markov, ['channeldb', optional('something')])

    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG':
            if ircmsgs.isAction(msg):
                s = ircmsgs.unAction(msg)
            else:
                s = msg.args[1]
            reply = []
            bananaProb = 0.1
            maybeBanana = False
            chance = random.random()
            self.log.debug("bananchance: "+str(chance)+" "+str(bananaProb)+" "+s)
            if chance < bananaProb:
                for word in s.split():
                    if maybeBanana:
                        maybeBanana = False
                        chance = random.random()
                        reply.append("banana")
                    else:
                        reply.append(word)
                    if word == "the":
                        maybeBanana = True
                if ircmsgs.isAction(msg):
                    msg = ircmsgs.action(msg.args[0], " ".join(reply), msg=msg)
                else:
                    msg = ircmsgs.IrcMsg(msg = msg, args=(msg.args[0], " ".join(reply)))
        return msg

Class = ArtificialIntelligence


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
