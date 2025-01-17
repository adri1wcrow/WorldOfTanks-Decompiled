# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/marathon/lunar_marathon_2022.py
from gui.impl.gen import R
from gui.marathon.marathon_event import MarathonEvent
from gui.marathon.marathon_event_container import MarathonEventContainer
from gui.marathon.marathon_event_controller import marathonCreator
from gui.Scaleform.locale.QUESTS import QUESTS

class LunarMarathonEvent(MarathonEvent):

    @property
    def label(self):
        return R.strings.quests.missions.tab.label.lunar_marathon()

    @property
    def tabTooltip(self):
        return QUESTS.MISSIONS_TAB_LUNAR_MARATHON

    @property
    def entryTooltip(self):
        return self._data.tooltips

    @property
    def tokenPrefix(self):
        return self._data.tokenPrefix

    @property
    def grindPostfix(self):
        return self._data.grindPostfix

    @property
    def proPostfix(self):
        return self._data.proPostfix

    @property
    def finishedPostfix(self):
        return self._data.finishedPostfix

    @property
    def packagePrefix(self):
        return self._data.packagePrefix

    @property
    def packageTemplate(self):
        return self._data.packageTemplate

    @property
    def packageStyleTemplate(self):
        return self._data.packageStyleTemplate

    @property
    def postPostfix(self):
        return self._data.postPostfix

    @property
    def stageDoneTemplate(self):
        return self._data.tokenPrefix + self._data.stageDonePostfix

    @property
    def isNeedHandlingEscape(self):
        return True

    def createMarathonWebHandlers(self):
        from gui.marathon.web_handlers import createDefaultMarathonWebHandlers
        return createDefaultMarathonWebHandlers()


@marathonCreator(LunarMarathonEvent)
class LunarMarathon(MarathonEventContainer):

    def _override(self):
        self.prefix = 'lunar_marathon'
        self.tokenPrefix = 'lunar_marathon:wz114_'
        self.styleTokenPostfix = 'style_discount'
        self.packagePrefix = 'wz114_'
        self.packageTemplate = 'wz114_vehicle_{}0d{}'
        self.packageStyleTemplate = 'wz114_3d_style{}'
        self.hangarFlagName = 'flag_marathon'
        self.grindPostfix = '_grind'
        self.proPostfix = '_pro'
        self.postPostfix = 'post_'
        self.finishedPostfix = '_v2'
        self.stageDonePostfix = '3d_style_q%STAGE%_done'
        self.questsInChain = 10
        self.minVehicleLevel = 6
        self.completedTokenPostfix = '_pass'
        self.questsPerStep = 3
        self.vehicleName = 'china:Ch45_WZ_114'
        self.rewardPostfix = '_reward'
        self.styleID = 303
        self.styleTokenDiscount = 12.5
