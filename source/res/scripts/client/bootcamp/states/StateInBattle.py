# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/bootcamp/states/StateInBattle.py
from AbstractState import AbstractState
from bootcamp.Assistant import BattleAssistant
from bootcamp.BootCampEvents import g_bootcampEvents
from bootcamp.scenery.Scenery import Scenery
from bootcamp.states import STATE
from bootcamp.BootcampConstants import UI_STATE
from gui.Scaleform.daapi.view.bootcamp.BCBattleSpaceEnv import BCBattleSpaceEnv
from gui.sounds.ambients import BattleSpaceEnv
from gui.app_loader.settings import GUI_GLOBAL_SPACE_ID as _SPACE_ID
from skeletons.gui.sounds import ISoundsController
from helpers import dependency

class StateInBattle(AbstractState):
    soundController = dependency.instance(ISoundsController)

    def __init__(self, lessonId, avatar, entities, bootcampGui):
        super(StateInBattle, self).__init__(STATE.IN_BATTLE)
        self.__assistant = BattleAssistant(avatar, lessonId, entities, bootcampGui)
        self.__lessonId = lessonId
        self.__avatar = avatar
        self.__scenery = Scenery(lessonId, self.__assistant)
        self.__oldSpaceEnv = None
        return

    def handleKeyEvent(self, event):
        return True

    def _doActivate(self):
        g_bootcampEvents.onUIStateChanged += self._onUIStateChanged
        self.__assistant.start()
        self.__scenery.start()
        self.__assistant.getMarkers().afterScenery()
        self.__oldSpaceEnv = self.soundController.setEnvForSpace(_SPACE_ID.BATTLE, BCBattleSpaceEnv)

    def onAvatarBecomeNonPlayer(self):
        if self.__assistant is not None:
            self.__assistant.stop()
        self.__avatar = None
        self.stopScenery()
        return

    def _doDeactivate(self):
        if self.__oldSpaceEnv is not None:
            self.soundController.setEnvForSpace(_SPACE_ID.BATTLE, self.__oldSpaceEnv)
        g_bootcampEvents.onUIStateChanged -= self._onUIStateChanged
        self._onUIStateChanged(UI_STATE.STOP)
        self.onAvatarBecomeNonPlayer()
        return

    def onBattleAction(self, actionId, actionParams):
        self.__assistant.onAction(actionId, actionParams)

    def stopScenery(self):
        if self.__scenery is not None:
            self.__scenery.stop()
            self.__scenery.destroy()
            self.__scenery = None
        return

    def deactivate(self):
        if self.__assistant is not None:
            self.__assistant = None
        return

    def _onUIStateChanged(self, state):
        if state == UI_STATE.STOP:
            self.stopScenery()
