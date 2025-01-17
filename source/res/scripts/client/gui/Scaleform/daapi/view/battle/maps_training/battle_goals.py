# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/battle/maps_training/battle_goals.py
import BigWorld
from constants import ARENA_PERIOD
from gui.Scaleform.daapi.view.battle.maps_training.battle_hints_mt import HintType
from gui.battle_control.arena_info.interfaces import IArenaVehiclesController
from gui.Scaleform.daapi.view.meta.MapsTrainingGoalsMeta import MapsTrainingGoalsMeta
from gui.battle_control.controllers.battle_hints_ctrl import BattleHintComponent
from helpers import dependency, isPlayerAvatar
from PlayerEvents import g_playerEvents
from items import vehicles
from maps_training_common.maps_training_constants import VEHICLE_CLASSES_ORDER
from skeletons.gui.battle_session import IBattleSessionProvider
from items.vehicles import VEHICLE_CLASS_TAGS
from skeletons.gui.game_control import IMapsTrainingController
from vehicle_systems.stricted_loading import makeCallbackWeak
from skeletons.account_helpers.settings_core import ISettingsCore
from account_helpers.settings_core.settings_constants import OnceOnlyHints

class MapsTrainingBattleGoals(BattleHintComponent, MapsTrainingGoalsMeta, IArenaVehiclesController):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)
    mapsTrainingController = dependency.descriptor(IMapsTrainingController)
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        super(MapsTrainingBattleGoals, self).__init__()
        self.goalsByType = {vehClass:{'vehClass': vehClass,
         'total': 0} for vehClass in VEHICLE_CLASS_TAGS}
        self._loaded = False

    def _populate(self):
        super(MapsTrainingBattleGoals, self)._populate()
        self.sessionProvider.addArenaCtrl(self)
        ctrl = self.sessionProvider.shared.feedback
        if ctrl is not None:
            ctrl.destroyGoal += self._destroyGoal
        if self.sessionProvider.shared.arenaPeriod.getPeriod() != ARENA_PERIOD.BATTLE:
            self.as_setVisibleS(False)
            g_playerEvents.onArenaPeriodChange += self._onArenaPeriodChange
        g_playerEvents.onRoundFinished += self.__onRoundFinished
        self.mapsTrainingController.requestInitialDataFromServer(makeCallbackWeak(self._setGoals))
        return

    def _dispose(self):
        self.sessionProvider.addArenaCtrl(self)
        ctrl = self.sessionProvider.shared.feedback
        if ctrl is not None:
            ctrl.destroyGoal -= self._destroyGoal
        g_playerEvents.onArenaPeriodChange -= self._onArenaPeriodChange
        g_playerEvents.onRoundFinished -= self.__onRoundFinished
        super(MapsTrainingBattleGoals, self)._dispose()
        return

    def __onRoundFinished(self, *args):
        self.as_setVisibleS(False)
        settings = self.settingsCore.serverSettings
        if not settings.getOnceOnlyHintsSetting(OnceOnlyHints.MAPS_TRAINING_NEWBIE_HINT, default=False):
            settings.setOnceOnlyHintsSettings({OnceOnlyHints.MAPS_TRAINING_NEWBIE_HINT: True})

    def _setGoals(self):
        if not isPlayerAvatar():
            return
        mapId = self.sessionProvider.arenaVisitor.type.getID()
        mapScenarios = self.mapsTrainingController.getConfig()['scenarios'][mapId]
        playerVehicle = self.sessionProvider.arenaVisitor.vehicles.getVehicleInfo(BigWorld.player().playerVehicleID)
        playerClass = vehicles.getVehicleClassFromVehicleType(playerVehicle['vehicleType'].type)
        playerTeam = playerVehicle['team']
        goals = mapScenarios[playerTeam][playerClass]['goals']
        sortedData = []
        for vehCls in VEHICLE_CLASSES_ORDER:
            goal = self.goalsByType[vehCls]
            goal['total'] = goals[vehCls]
            sortedData.append(goal)

        self.as_updateS(sortedData)

    def _getSoundNotification(self, hint, data):
        return hint.soundNotificationNewbie if hint.soundNotificationNewbie is not None and not self.settingsCore.serverSettings.getOnceOnlyHintsSetting(OnceOnlyHints.MAPS_TRAINING_NEWBIE_HINT, default=False) else hint.soundNotification

    def _showHint(self, hintData):
        hintType = hintData['hintType']
        descr = hintData.get('description1')
        if hintType is HintType.GOAL:
            descr = descr.format(count=hintData['targetsCount'], total=hintData['targetsTotal'])
        if hintType is HintType.TIMER_GREEN:
            self.as_showHintS(hintType.value, hintData.get('description2'), descr)
        else:
            self.as_showHintS(hintType.value, descr)

    def _hideHint(self):
        self.as_hideHintS()

    def _destroyGoal(self, vehType):
        self.as_destroyGoalS(vehType)

    def _onArenaPeriodChange(self, period, *args):
        if period == ARENA_PERIOD.BATTLE:
            self.as_setVisibleS(True)
            g_playerEvents.onArenaPeriodChange -= self._onArenaPeriodChange
