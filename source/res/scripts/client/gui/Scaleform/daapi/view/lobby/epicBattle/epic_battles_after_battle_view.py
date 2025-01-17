# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/epicBattle/epic_battles_after_battle_view.py
import SoundGroups
from constants import EPIC_ABILITY_PTS_NAME
from gui.Scaleform.daapi.view.lobby.epicBattle.after_battle_reward_view_helpers import getProgressionIconVODict, getQuestBonuses, getFinishBadgeBonuses
from gui.Scaleform.daapi.view.lobby.missions.awards_formatters import EpicCurtailingAwardsComposer
from gui.Scaleform.daapi.view.meta.EpicBattlesAfterBattleViewMeta import EpicBattlesAfterBattleViewMeta
from gui.impl.gen.view_models.views.battle_royale.battle_results.personal.battle_reward_item_model import BattleRewardItemModel
from gui.impl import backport
from gui.impl.gen import R
from gui.server_events.awards_formatters import getEpicViewAwardPacker, AWARDS_SIZES
from gui.server_events.bonuses import EpicAbilityPtsBonus, mergeBonuses, splitBonuses
from gui.shared.formatters import text_styles
from gui.shared.utils import toUpper
from gui.sounds.epic_sound_constants import EPIC_METAGAME_WWISE_SOUND_EVENTS
from helpers import dependency
from skeletons.gui.game_control import IEpicBattleMetaGameController, IBattlePassController
from skeletons.gui.server_events import IEventsCache

class EpicBattlesAfterBattleView(EpicBattlesAfterBattleViewMeta):
    _MAX_VISIBLE_AWARDS = 6
    _awardsFormatter = EpicCurtailingAwardsComposer(_MAX_VISIBLE_AWARDS, getEpicViewAwardPacker())
    __eventsCache = dependency.descriptor(IEventsCache)
    __epicController = dependency.descriptor(IEpicBattleMetaGameController)
    __battlePass = dependency.descriptor(IBattlePassController)

    def __init__(self, ctx=None):
        super(EpicBattlesAfterBattleView, self).__init__()
        self.__ctx = ctx
        self.__maxLvlReached = False
        self.__isProgressBarAnimating = False

    def onIntroStartsPlaying(self):
        SoundGroups.g_instance.playSound2D(EPIC_METAGAME_WWISE_SOUND_EVENTS.EB_ACHIEVED_RANK)

    def onRibbonStartsPlaying(self):
        if not self.__maxLvlReached:
            SoundGroups.g_instance.playSound2D(EPIC_METAGAME_WWISE_SOUND_EVENTS.EB_LEVEL_REACHED)
        else:
            SoundGroups.g_instance.playSound2D(EPIC_METAGAME_WWISE_SOUND_EVENTS.EB_LEVEL_REACHED_MAX)

    def onEscapePress(self):
        self.destroy()

    def onCloseBtnClick(self):
        self.destroy()

    def onWindowClose(self):
        self.destroy()

    def onProgressBarStartAnim(self):
        if not self.__isProgressBarAnimating:
            SoundGroups.g_instance.playSound2D(EPIC_METAGAME_WWISE_SOUND_EVENTS.EB_PROGRESS_BAR_START)
            self.__isProgressBarAnimating = True

    def onProgressBarCompleteAnim(self):
        if self.__isProgressBarAnimating:
            SoundGroups.g_instance.playSound2D(EPIC_METAGAME_WWISE_SOUND_EVENTS.EB_PROGRESS_BAR_STOP)
            self.__isProgressBarAnimating = False

    def destroy(self):
        self.onProgressBarCompleteAnim()
        super(EpicBattlesAfterBattleView, self).destroy()

    def _populate(self):
        super(EpicBattlesAfterBattleView, self)._populate()
        epicMetaGame = self.__ctx['reusableInfo'].personal.avatar.extensionInfo
        pMetaLevel, pFamePts = epicMetaGame.get('metaLevel', (None, None))
        prevPMetaLevel, prevPFamePts = epicMetaGame.get('prevMetaLevel', (None, None))
        boosterFLXP = epicMetaGame.get('boosterFlXP', 0)
        originalFlXP = epicMetaGame.get('originalFlXP', 0)
        maxMetaLevel = self.__epicController.getMaxPlayerLevel()
        famePtsToProgress = self.__epicController.getLevelProgress()
        season = self.__epicController.getCurrentSeason() or None
        cycleNumber = 0
        if season is not None:
            cycleNumber = self.__epicController.getCurrentOrNextActiveCycleNumber(season)
        famePointsReceived = sum(famePtsToProgress[prevPMetaLevel:pMetaLevel]) + pFamePts - prevPFamePts
        achievedRank = max(epicMetaGame.get('playerRank', 0), 1)
        rankNameId = R.strings.epic_battle.rank.dyn('rank' + str(achievedRank))
        rankName = toUpper(backport.text(rankNameId())) if rankNameId.exists() else ''
        awardsVO = self._awardsFormatter.getFormattedBonuses(self.__getBonuses(prevPMetaLevel, pMetaLevel), size=AWARDS_SIZES.BIG)
        fameBarVisible = True
        dailyQuestAvailable = False
        if prevPMetaLevel >= maxMetaLevel or pMetaLevel >= maxMetaLevel:
            boosterFLXP = famePointsReceived - originalFlXP if famePointsReceived > originalFlXP else 0
            if prevPMetaLevel >= maxMetaLevel:
                fameBarVisible = False
            else:
                self.__maxLvlReached = True
        lvlReachedText = toUpper(backport.text(R.strings.epic_battle.epic_battles_after_battle.Level_Up_Title(), level=pMetaLevel))
        data = {'awards': awardsVO,
         'progress': self.__getProgress(pMetaLevel, pFamePts, prevPMetaLevel, prevPFamePts, maxMetaLevel, boosterFLXP),
         'barText': '+' + str(min(originalFlXP, famePointsReceived)),
         'barBoostText': '+' + str(boosterFLXP),
         'epicMetaLevelIconData': getProgressionIconVODict(cycleNumber, pMetaLevel),
         'rank': achievedRank,
         'rankText': text_styles.epicTitle(rankName),
         'rankSubText': text_styles.promoTitle(backport.text(R.strings.epic_battle.epic_battles_after_battle.Achieved_Rank())),
         'levelUpText': text_styles.heroTitle(lvlReachedText),
         'backgroundImageSrc': backport.image(R.images.gui.maps.icons.epicBattles.backgrounds.back_congrats()),
         'fameBarVisible': fameBarVisible,
         'maxLevel': maxMetaLevel,
         'maxLvlReached': self.__maxLvlReached,
         'questPanelVisible': dailyQuestAvailable}
        self.as_setDataS(data)
        return

    def __getBonuses(self, prevLevel, currentLevel):
        questsProgressData = self.__ctx['reusableInfo'].personal.getQuestsProgress()
        if currentLevel == self.__epicController.getMaxPlayerLevel():
            bonuses = getFinishBadgeBonuses(questsProgressData, self.__epicController.FINAL_BADGE_QUEST_ID)
        else:
            bonuses = []
        bonuses.extend(getQuestBonuses(questsProgressData, (self.__epicController.TOKEN_QUEST_ID,), self.__epicController.TOKEN_QUEST_ID + str(currentLevel)))
        if self.__battlePass.getCurrentLevel() == self.__battlePass.getMaxLevel():
            excluded = [BattleRewardItemModel.BATTLE_PASS_POINTS]
            bonuses = [ b for b in bonuses if b.getName() not in excluded ]
        for level in range(prevLevel + 1, currentLevel + 1):
            bonuses.extend(self.__getAbilityPointsRewardBonus(level))

        bonuses = mergeBonuses(bonuses)
        bonuses = splitBonuses(bonuses)
        return bonuses

    def __getAbilityPointsRewardBonus(self, level):
        abilityPts = self.__epicController.getAbilityPointsForLevel()
        return [EpicAbilityPtsBonus(name=EPIC_ABILITY_PTS_NAME, value=abilityPts[level - 1])] if level and level <= len(abilityPts) else []

    def __getProgress(self, curLevel, curFamePoints, prevLevel, prevFamePoints, maxLevel, boostedXP):
        getPointsProgressForLevel = self.__epicController.getPointsProgressForLevel
        originalXP = curFamePoints - boostedXP
        pLevel = prevLevel + float(prevFamePoints) / float(getPointsProgressForLevel(prevLevel)) if prevLevel != maxLevel else maxLevel
        cLevel = curLevel + float(originalXP) / float(getPointsProgressForLevel(curLevel)) if curLevel != maxLevel else maxLevel
        if boostedXP:
            if curLevel == maxLevel:
                cLevel = maxLevel - float(boostedXP) / float(getPointsProgressForLevel(curLevel - 1))
            cBoostedLevel = curLevel + float(curFamePoints) / float(getPointsProgressForLevel(curLevel)) if curLevel != maxLevel else maxLevel
        else:
            cBoostedLevel = cLevel
        return (pLevel, cLevel, cBoostedLevel)
