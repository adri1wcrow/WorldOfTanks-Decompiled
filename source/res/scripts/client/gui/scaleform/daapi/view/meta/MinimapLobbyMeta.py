# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/MinimapLobbyMeta.py
from gui.Scaleform.daapi.view.meta.MinimapEntityMeta import MinimapEntityMeta

class MinimapLobbyMeta(MinimapEntityMeta):
    """
    DO NOT MODIFY!
    Generated with yaml.
    __author__ = 'yaml_processor'
    @extends MinimapEntityMeta
    null
    """

    def setMap(self, arenaID):
        """
        :param arenaID:
        :return :
        """
        self._printOverrideError('setMap')

    def setMinimapData(self, arenaID, playerTeam, size):
        """
        :param arenaID:
        :param playerTeam:
        :param size:
        :return :
        """
        self._printOverrideError('setMinimapData')

    def as_changeMapS(self, texture):
        """
        :param texture:
        :return :
        """
        return self.flashObject.as_changeMap(texture) if self._isDAAPIInited() else None

    def as_addPointS(self, x, y, type, color, id):
        """
        :param x:
        :param y:
        :param type:
        :param color:
        :param id:
        :return :
        """
        return self.flashObject.as_addPoint(x, y, type, color, id) if self._isDAAPIInited() else None

    def as_clearS(self):
        """
        :return :
        """
        return self.flashObject.as_clear() if self._isDAAPIInited() else None
