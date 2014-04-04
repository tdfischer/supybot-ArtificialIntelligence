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

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('ArtificialIntelligence', True)


ArtificialIntelligence = conf.registerPlugin('ArtificialIntelligence')
conf.registerChannelValue(ArtificialIntelligence, 'ignoreBotCommands',
    registry.Boolean(False, """Determines whether messages addressed to the
    bot are ignored."""))
conf.registerChannelValue(ArtificialIntelligence, 'minChainLength',
    registry.PositiveInteger(1, """Determines the length of the smallest chain
    which the markov command will generate."""))
conf.registerChannelValue(ArtificialIntelligence, 'maxAttempts',
    registry.PositiveInteger(1, """Determines the maximum number of times the
    bot will attempt to generate a chain that meets or exceeds the size set in
    minChainLength."""))

conf.registerGroup(ArtificialIntelligence, 'randomSpeaking')
conf.registerChannelValue(ArtificialIntelligence.randomSpeaking,
    'probability', registry.Probability(0, """Determines the probability that
    will be checked against to determine whether the bot should randomly say
    something.  If 0, the bot will never say anything on it's own.  If 1, the
    bot will speak every time we make a check."""))
conf.registerChannelValue(ArtificialIntelligence.randomSpeaking,
    'maxDelay', registry.PositiveInteger(10, """Determines the upper bound for
    how long the bot will wait before randomly speaking.  The delay is a
    randomly generated number of seconds below the value of this config
    variable."""))
conf.registerChannelValue(ArtificialIntelligence.randomSpeaking,
    'throttleTime', registry.PositiveInteger(300, """Determines the minimum
    number of seconds between the bot randomly speaking."""))
conf.registerChannelValue(ArtificialIntelligence.randomSpeaking,
    'bananaChance', registry.Probability(0.1, """Determines the probability that
    will be checked against to determined whether the bot should randomly
    replace certain words with "banana"."""))
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(ArtificialIntelligence, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
