import logging


class TurnAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra, bot):
        logging.LoggerAdapter.__init__(self,logger,extra)
        self.bot = bot

    def process(self, msg, kwargs):
        msg, kwargs = logging.LoggerAdapter.process(self,msg, kwargs)
        kwargs["extra"]["turn"] = self.bot.turn
        return msg, kwargs
