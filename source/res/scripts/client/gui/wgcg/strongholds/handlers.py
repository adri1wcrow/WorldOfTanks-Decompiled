# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/wgcg/strongholds/handlers.py
from gui.wgcg.base.handlers import RequestHandlers
from gui.wgcg.settings import WebRequestDataType
from helpers import dependency
from skeletons.connection_mgr import IConnectionManager

class StrongholdsRequestHandlers(RequestHandlers):
    connectionMgr = dependency.descriptor(IConnectionManager)

    def get(self):
        handlers = {WebRequestDataType.STRONGHOLD_LEAVE: self.__leave,
         WebRequestDataType.STRONGHOLD_ASSIGN: self.__assign,
         WebRequestDataType.STRONGHOLD_UNASSIGN: self.__unassign,
         WebRequestDataType.STRONGHOLD_CHANGE_OPENED: self.__changeOpened,
         WebRequestDataType.STRONGHOLD_SET_VEHICLE: self.__setVehicle,
         WebRequestDataType.STRONGHOLD_SET_PLAYER_STATE: self.__setPlayerState,
         WebRequestDataType.STRONGHOLD_SEND_INVITE: self.__sendInvite,
         WebRequestDataType.STRONGHOLD_KICK: self.__kick,
         WebRequestDataType.STRONGHOLD_BATTLE_QUEUE: self.__battleQueue,
         WebRequestDataType.STRONGHOLD_GIVE_LEADERSHIP: self.__giveLeadership,
         WebRequestDataType.STRONGHOLD_TAKE_LEADERSHIP: self.__takeLeadership,
         WebRequestDataType.STRONGHOLD_SET_RESERVE: self.__setReserve,
         WebRequestDataType.STRONGHOLD_UNSET_RESERVE: self.__unsetReserve,
         WebRequestDataType.STRONGHOLD_UPDATE: self.__updateStronghold,
         WebRequestDataType.STRONGHOLD_STATISTICS: self.__getStrongholdStatistics,
         WebRequestDataType.STRONGHOLD_JOIN_BATTLE: self.__joinBattle,
         WebRequestDataType.STRONGHOLD_SET_EQUIPMENT_COMMANDER: self.__setEquipmentCommander}
        return handlers

    def __assign(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'assign_player'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getPlayerID(), ctx.getSlotIdx())

    def __unassign(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'unassign_player'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getPlayerID())

    def __changeOpened(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'set_open'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.isOpened())

    def __setVehicle(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'set_vehicle'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getVehTypeCD())

    def __setPlayerState(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'set_readiness'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.isReady(), False)

    def __sendInvite(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'invite_players'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getDatabaseIDs(), ctx.getComment())

    def __kick(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'kick_player'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getPlayerID())

    def __battleQueue(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'set_readiness'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.isRequestToStart(), False)

    def __giveLeadership(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'give_leadership'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getPlayerID())

    def __takeLeadership(self, ctx, callback):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'take_away_leadership'), self.__getPeripheryIDStr(), ctx.getUnitMgrID())

    def __setReserve(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'lock_reserve'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getReserveID())

    def __setEquipmentCommander(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'set_equipment_commander'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getPlayerID())

    def __unsetReserve(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'unlock_reserve'), self.__getPeripheryIDStr(), ctx.getUnitMgrID(), ctx.getReserveID())

    def __leave(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'leave_room'), self.__getPeripheryIDStr(), ctx.getUnitMgrID())

    def __updateStronghold(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'get_wgsh_unit_info'), self.__getPeripheryIDStr(), ctx.getUnitMgrID())

    def __joinBattle(self, ctx, callback, *args, **kwargs):
        self._requester.doRequestEx(ctx, callback, ('wgsh', 'join_room'), self.__getPeripheryIDStr(), ctx.getUnitMgrID())

    def __getStrongholdStatistics(self, ctx, callback):
        return self._requester.doRequestEx(ctx, callback, ('wgsh', 'clan_statistics'), clan_id=ctx.getClanID())

    def __getPeripheryIDStr(self):
        return str(self.connectionMgr.peripheryID)
