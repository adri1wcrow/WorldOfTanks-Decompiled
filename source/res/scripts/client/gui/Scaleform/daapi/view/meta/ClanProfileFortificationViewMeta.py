# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ClanProfileFortificationViewMeta.py
from gui.Scaleform.daapi.view.lobby.clans.profile.ClanProfileBaseView import ClanProfileBaseView

class ClanProfileFortificationViewMeta(ClanProfileBaseView):
    """
    DO NOT MODIFY!
    Generated with yaml.
    __author__ = 'yaml_processor'
    @extends ClanProfileBaseView
    null
    """

    def as_showBodyDummyS(self, data):
        """
        :param data:
        :return :
        """
        return self.flashObject.as_showBodyDummy(data) if self._isDAAPIInited() else None

    def as_hideBodyDummyS(self):
        """
        :return :
        """
        return self.flashObject.as_hideBodyDummy() if self._isDAAPIInited() else None
