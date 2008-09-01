#   
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
#
# $Id: database.py 36 2008-04-15 12:22:06Z oroussy $
#
# This file is part of MMC.
#
# MMC is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MMC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MMC; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
from mmc.support.mmctools import Singleton
from sqlalchemy import *
from sqlalchemy.exceptions import SQLError
from mmc.plugins.pulse2.group import ComputerGroupManager


# USAGE :
#    def getAllMachines():
#        ...
#            # filtering on query
#            join_query, query_filter = filter(self.machine, filt)
#        ...

class DyngroupDatabaseHelper(Singleton):
    def init(self):
        #self.logger = logging.getLogger()
        self.filters = {}

    def filter(self, ctx, join_query, filt, query, grpby, filters = None):
        if filters != None:
            self.filters[ctx.userid] = and_(*filters)
        query_filter = None
        try:
            if not filt.has_key('query'):
                return (join_query, query_filter)
            query_filter, join_tables = self.__treatQueryLevel(ctx, query, grpby, join_query, filt['query'])
            for table in join_tables:
                join_query = join_query.join(table)
        except KeyError, e:
            self.logger.error(e)
        except TypeError, e:
            self.logger.error(e)
       
        return (join_query, query_filter)

    def __treatQueryLevel(self, ctx, query, grpby, join_query, queries, join_tables = [], invert = False):
        """
        Use recursively by getAllMachines to build the query
        Used in the dyngroup context, to build AND, OR and NOT queries
        """
        bool = queries[0]
        level = queries[1]
        if bool == 'OR':
            query_filter, join_tables = self.__treatQueryLevelOR(ctx, query, grpby, join_query, level, join_tables, invert)
        elif bool == 'AND':
            query_filter, join_tables = self.__treatQueryLevelAND(ctx, query, grpby, join_query, level, join_tables, invert)
        elif bool == 'NOT':
            query_filter, join_tables = self.__treatQueryLevelNOT(ctx, query, grpby, join_query, level, join_tables, invert)
        else:
            self.logger.error("Don't know this kind of bool operation : %s" % (bool))
        return (query_filter, join_tables)

    def __treatQueryLevelOR(self, ctx, query, grpby, join_query, queries, join_tables, invert = False):
        """
        Build OR queries
        """
        filter_on = []
        for q in queries:
            if len(q) == 4:
                if q[1] == 'dyngroup':
                    join_tab = self.computersTable()
                    computers = ComputerGroupManager().result_group_by_name(ctx, q[3])
                    filt = self.computersMapping(computers, invert)
                else:
                    join_tab = self.mappingTable(q)
                    filt = self.mapping(q, invert)
                join_q = join_query
                if type(join_tab) == list:
                    for table in join_tab:
                        if table != join_query:
                            join_q = join_q.join(table)
                else:
                    join_q = join_q.join(join_tab)

                q = query.add_column(grpby).select_from(join_q).filter(filt)
                if self.filters.has_key(ctx.userid):
                    q = q.filter(self.filters[ctx.userid])
                q = q.group_by(grpby).all()
                res = map(lambda x: x[1], q)
                filter_on.append(grpby.in_(*res))
            else:
                query_filter, join_tables = self.__treatQueryLevel(ctx, query, grpby, join_query, q, join_tables)
                filter_on.append(query_filter)
        query_filter = or_(*filter_on)
        return (query_filter, join_tables)

    def __treatQueryLevelAND(self, ctx, query, grpby, join_query, queries, join_tables, invert = False):
        """
        Build AND queries
        """
        filter_on = []
        for q in queries:
            if len(q) == 4:
                if q[1] == 'dyngroup':
                    join_tab = self.computersTable()
                    computers = ComputerGroupManager().result_group_by_name(ctx, q[3])
                    filt = self.computersMapping(computers, invert)
                else:
                    join_tab = self.mappingTable(q)
                    filt = self.mapping(q, invert)
                join_q = join_query
                if type(join_tab) == list:
                    for table in join_tab:
                        if table != join_query:
                            join_q = join_q.join(table)
                else:
                    join_q = join_q.join(join_tab)

                q = query.add_column(grpby).select_from(join_q).filter(filt)
                if self.filters.has_key(ctx.userid):
                    q = q.filter(self.filters[ctx.userid])
                q = q.group_by(grpby).all()
                res = map(lambda x: x[1], q)
                filter_on.append(grpby.in_(*res))
            else:
                query_filter, join_tables = self.__treatQueryLevel(ctx, query, grpby, join_query, q, join_tables)
                filter_on.append(query_filter)
        query_filter = and_(*filter_on)
        return (query_filter, join_tables)

    def __treatQueryLevelNOT(self, ctx, query, grpby, join_query, queries, join_tables, invert = False):
        """
        Build NOT queries : it switches the invert flag
        """
        filter_on = []
        for q in queries:
            if len(q) == 4:
                if q[1] == 'dyngroup':
                    join_tab = self.computersTable()
                    computers = ComputerGroupManager().result_group_by_name(ctx, q[3])
                    filt = self.computersMapping(computers, invert)
                else:
                    join_tab = self.mappingTable(q)
                    filt = self.mapping(q, invert)
                join_q = join_query
                if type(join_tab) == list:
                    for table in join_tab:
                        if table != join_query:
                            join_q = join_q.join(table)
                else:
                    join_q = join_q.join(join_tab)
                                            
                query = query.add_column(grpby).select_from(join_q).filter(filt)
                if self.filters.has_key(ctx.userid):
                    q = q.filter(self.filters[ctx.userid])
                q = q.group_by(grpby).all()
                res = map(lambda x: x[1], query)
                filter_on.append(not_(grpby.in_(*res)))
            else:
                query_filter, join_tables = self.__treatQueryLevel(ctx, query, grpby, join_query, q, join_tables, not invert)
                filter_on.append(query_filter)
        query_filter = and_(*filter_on)
        return (query_filter, join_tables)

    def __mappingTables(self, queries):
        """
        Map multiple tables (use mappingTable)
        """
        ret = []
        for query in queries:
            if len(query) == 4:
                self.mappingTable(query)
        return ret

    def mappingTable(self, query):
        """
        Map a table name on a table mapping

        get the dyngroup format query

        return the mapped sqlalchemy table from the third field in the query struct
        """
        raise "mappingTable has to be defined"

    def mapping(self, query, invert = False):
        """
        Map a name and request parameters on a sqlalchemy request

        get the dyngroup format query
        get a flag saying if we want to map on the value or not to map on the value

        return the sqlalchemy equation to exec in a select_from()
        """
        raise "mapping has to be defined"
 
    def computersTable(self):
        """
        return the computers table mapping

        return the mapped sqlalchemy table for computer
        """
        raise "computersTable has to be defined"

    def computersMapping(self, computers, invert = False):
        """
        Map the computer object on the good field in the database

        get the list of computers we want to map
        get a flag saying if we want to map on the value or not to map on the value

        return the sqlalchemy equation to exec in a select_from()
        """
        raise "computersMapping has to be defined"
       
############################################
## specific code has to be defined 
## for these two last method
############################################
#
#    def mappingTable(self, query):
#        """
#        Map a table name on a table mapping
#        """
#        if query[2] == 'OS':
#            return self.os
#        elif query[2] == 'ENTITY':
#            return self.location
#        elif query[2] == 'SOFTWARE':
#            return [self.inst_software, self.licenses, self.software]
#        return []
#
#    def mapping(self, query, invert = False):
#        """
#        Map a name and request parameters on a sqlalchemy request
#        """
#        if query[2] == 'OS':
#            if invert:
#                return self.os.c.name != query[3]
#            else:
#                return self.os.c.name == query[3]
#        elif query[2] == 'ENTITY':
#            if invert:
#                return self.location.c.name != query[3]
#            else:
#                return self.location.c.name == query[3]
#        elif query[2] == 'SOFTWARE':
#            if invert:
#                return self.software.c.name != query[3]
#            else:
#                return self.software.c.name == query[3]


def onlyAddNew(obj, value, main):
    if type(value) == list:
        for i in value:
            try:
                obj.index(i)
            except:
                if i != main:
                    obj.append(i)
    else:
        try:
            obj.index(value)
        except:
            if value != main:
                obj.append(value)
    return obj

