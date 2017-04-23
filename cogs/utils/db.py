#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import ujson as json
import asyncpg
import copy


class Database(object):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def dump(data):
        return json.dumps(data).replace("'", "''")

    async def connect(self):
        self._conn = await asyncpg.connect(user='root', password='root',
                                           database='pokerpg', host='127.0.0.1')

    # User functions
    ########################################################################
    async def user_insert(self, member, data):
        """Create a new user entry with the given data"""
        jd = self.dump({member.guild.id: data})
        req = f"""INSERT INTO userdata (UUID, info) VALUES ({member.id}, '{jd}')"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def user_select(self, member):
        """Select a user's data for a specified server"""
        req = f"""SELECT info -> '{member.guild.id}' FROM userdata WHERE UUID = {member.id}"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def user_update(self, member, data):
        """Update a user's data for a specific server"""
        jd = self.dump(data)
        req = f"""UPDATE userdata -> '{member.guild.id}'
        SET info = '{jd}'
        WHERE UUID = {member.id}"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def user_exists(self, member):
        """Check if a user has an entry in the db"""
        req = f"""SELECT info FROM userdata WHERE UUID = {member.id}"""
        return bool(await self._conn.fetchval(req))

    async def add_user(self, member, data=None):
        """Add a server to the users json, if the user doesnt exist user_insert to make one"""
        if not data:
            data = {member.guild.id: self.bot.default_udata}

        if not await self.user_exists(member):
            await self.user_insert(member, data)
            return

        else:
            values = await self.user_select(member)

        if not values:
            await self.user_update(member, data)

    async def update_user_data(self, member, data):
        """Update a user's server data"""
        if await self.user_select(member):
            await self.user_update(member, data)
        else:
            await self.user_insert(member, data)

    async def get_user_data(self, member):
        """Get a user's data for a server"""
        data = await self.user_select(member)
        return data if data else copy.copy(self.bot.default_udata)

    async def get_all_user_data(self, member):
        """Get a user's data for all servers"""
        req = f"""SELECT info FROM userdata WHERE UUID = {member.id}"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    # Server functions
    ########################################################################
    async def guild_insert(self, guild, data):
        """Add a new guild to the db"""
        jd = self.dump(data)
        req = f"""INSERT INTO servdata (UUID, info) VALUES ({guild.id}, '{jd}')"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def guild_select(self, guild):
        """Get a guild from the db"""
        req = f"""SELECT info FROM servdata WHERE UUID = {guild.id}"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def guild_update(self, guild, data):
        """Update a guild"""
        jd = self.dump(data)
        req = f"""UPDATE servdata
        SET info = '{jd}'
        WHERE UUID = {guild.id}"""
        response = await self._conn.fetchval(req)
        return json.decode(response) if response else response

    async def add_guild(self, guild, data=None):
        """Add a guild to the db"""
        values = await self.guild_select(guild)
        if values:
            return

        if not data:
            data = self.bot.default_servdata

        await self.guild_insert(guild, data)

    async def update_guild_data(self, guild, data):
        if await self.guild_select(guild):
            await self.guild_update(guild, data)
        else:
            await self.guild_insert(guild, data)

    async def get_guild_data(self, guild):
        values = await self.guild_select(guild)
        if values:
            return values
        else:
            await self.guild_insert(guild, self.bot.default_servdata)
            return await self.get_guild_data(guild)