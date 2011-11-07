import logging


class TurnAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra, bot):
        super(TurnAdapter,self).__init__(logger,extra)
        self.bot = bot

    def process(self, msg, kwargs):
        msg, kwargs = super(TurnAdapter,self).process(msg, kwargs)
        kwargs["extra"]["turn"] = self.bot.turn
        return msg, kwargs
