# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/BattleHintPanelMeta.py
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent

class BattleHintPanelMeta(BaseDAAPIComponent):

    def onPlaySound(self, soundType):
        self._printOverrideError('onPlaySound')

    def onHideComplete(self):
        self._printOverrideError('onHideComplete')

    def as_setDataS(self, key, messageLeft, messageRight, offsetX, offsetY, reducedPanning):
        return self.flashObject.as_setData(key, messageLeft, messageRight, offsetX, offsetY, reducedPanning) if self._isDAAPIInited() else None

    def as_toggleS(self, isShow):
        return self.flashObject.as_toggle(isShow) if self._isDAAPIInited() else None
