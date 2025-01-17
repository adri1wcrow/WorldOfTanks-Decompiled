# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/HangarMeta.py
from gui.Scaleform.framework.entities.View import View

class HangarMeta(View):

    def onEscape(self):
        self._printOverrideError('onEscape')

    def onCloseBtnClick(self):
        self._printOverrideError('onCloseBtnClick')

    def showHelpLayout(self):
        self._printOverrideError('showHelpLayout')

    def closeHelpLayout(self):
        self._printOverrideError('closeHelpLayout')

    def hideTeaser(self):
        self._printOverrideError('hideTeaser')

    def onTeaserClick(self):
        self._printOverrideError('onTeaserClick')

    def as_setCrewEnabledS(self, value):
        return self.flashObject.as_setCrewEnabled(value) if self._isDAAPIInited() else None

    def as_setCarouselEnabledS(self, value):
        return self.flashObject.as_setCarouselEnabled(value) if self._isDAAPIInited() else None

    def as_setupAmmunitionPanelS(self, data):
        return self.flashObject.as_setupAmmunitionPanel(data) if self._isDAAPIInited() else None

    def as_setControlsVisibleS(self, value):
        return self.flashObject.as_setControlsVisible(value) if self._isDAAPIInited() else None

    def as_setVisibleS(self, value):
        return self.flashObject.as_setVisible(value) if self._isDAAPIInited() else None

    def as_showHelpLayoutS(self):
        return self.flashObject.as_showHelpLayout() if self._isDAAPIInited() else None

    def as_closeHelpLayoutS(self):
        return self.flashObject.as_closeHelpLayout() if self._isDAAPIInited() else None

    def as_showMiniClientInfoS(self, description, hyperlink):
        return self.flashObject.as_showMiniClientInfo(description, hyperlink) if self._isDAAPIInited() else None

    def as_show3DSceneTooltipS(self, id, args):
        return self.flashObject.as_show3DSceneTooltip(id, args) if self._isDAAPIInited() else None

    def as_hide3DSceneTooltipS(self):
        return self.flashObject.as_hide3DSceneTooltip() if self._isDAAPIInited() else None

    def as_setCarouselS(self, linkage, alias):
        return self.flashObject.as_setCarousel(linkage, alias) if self._isDAAPIInited() else None

    def as_setAlertMessageBlockVisibleS(self, isVisible):
        return self.flashObject.as_setAlertMessageBlockVisible(isVisible) if self._isDAAPIInited() else None

    def as_showTeaserS(self, data):
        return self.flashObject.as_showTeaser(data) if self._isDAAPIInited() else None

    def as_setTeaserTimerS(self, timeLabel):
        return self.flashObject.as_setTeaserTimer(timeLabel) if self._isDAAPIInited() else None

    def as_hideTeaserTimerS(self):
        return self.flashObject.as_hideTeaserTimer() if self._isDAAPIInited() else None

    def as_setNotificationEnabledS(self, value):
        return self.flashObject.as_setNotificationEnabled(value) if self._isDAAPIInited() else None

    def as_setEnvelopesVisibleS(self, value):
        return self.flashObject.as_setEnvelopesVisible(value) if self._isDAAPIInited() else None

    def as_setLootboxesVisibleS(self, value):
        return self.flashObject.as_setLootboxesVisible(value) if self._isDAAPIInited() else None

    def as_createDQWidgetS(self):
        return self.flashObject.as_createDQWidget() if self._isDAAPIInited() else None

    def as_destroyDQWidgetS(self):
        return self.flashObject.as_destroyDQWidget() if self._isDAAPIInited() else None

    def as_showSwitchToAmmunitionS(self):
        return self.flashObject.as_showSwitchToAmmunition() if self._isDAAPIInited() else None

    def as_toggleBattleRoyaleS(self, isBattleRoyale):
        return self.flashObject.as_toggleBattleRoyale(isBattleRoyale) if self._isDAAPIInited() else None

    def as_toggleCnSubscriptionS(self, isCnSubscription):
        return self.flashObject.as_toggleCnSubscription(isCnSubscription) if self._isDAAPIInited() else None

    def as_setDQWidgetLayoutS(self, lyout):
        return self.flashObject.as_setDQWidgetLayout(lyout) if self._isDAAPIInited() else None

    def as_setShopSalesVisibleS(self, value):
        return self.flashObject.as_setShopSalesVisible(value) if self._isDAAPIInited() else None
