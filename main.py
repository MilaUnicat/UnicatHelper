from datetime import date

import discord
from discord.ext import commands
import base
from PrivilegedUsers import PrivilegedUsers
from Teams import Teams
from UserPoints import UserPoints
from Quotes import Quote
from CustomChanges import CustomChanges
from EnabledFeatures import EnabledFeatures
import os
from dotenv import load_dotenv
from sqlalchemy import insert, delete, update
import util
import random

load_dotenv()

description = '''Hello'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


def custom_prefix(ctx, message: discord.Message):
    session = base.Session()
    prefix = session.query(CustomChanges.command_prefix)\
        .filter(CustomChanges.server_id == message.guild.id)\
        .one_or_none()
    if prefix is None:
        prefix = '?'
    return prefix


bot = commands.Bot(command_prefix=custom_prefix, description=description, intents=intents)
ran_num = random


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def help_me(ctx):
    await ctx.send(util.help_text())


@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')


@bot.group()
async def setup(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f'You need to provide a subcommand')


@setup.command()
async def prefix(ctx, alias):
    if len(alias) == 1:
        if ctx.guild.owner_id == ctx.author.id:
            session = base.Session()
            current = session.query(CustomChanges.command_prefix)\
                .filter(CustomChanges.server_id == ctx.guild.id)\
                .one_or_none()
            if current is None:
                stmt = insert(CustomChanges)\
                    .values(server_id=ctx.guild.id, command_prefix=alias)
            else:
                stmt = update(CustomChanges)\
                    .where(CustomChanges.server_id == ctx.guild.id)\
                    .values(command_prefix=alias)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'New command prefix is now {alias}')
        else:
            await ctx.send(f'Only the server owner can update prefix!')
    else:
        await ctx.send(f'Alias must be only one character!')


@setup.group()
async def feature(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f'You need to provide a subcommand')


@feature.command()
async def points(ctx, enabled='on'):
    session = base.Session()
    message = util.enable_disable_feature(session=session, ctx=ctx, enabled=enabled, feature='points')
    if message is not None:
        await ctx.send(message)


@feature.command()
async def quote(ctx, enabled='on'):
    session = base.Session()
    message = util.enable_disable_feature(session=session, ctx=ctx, enabled=enabled, feature='quote')
    if message is not None:
        await ctx.send(message)


@bot.group()
async def points(ctx):
    session = base.Session()
    points_enabled = session.query(EnabledFeatures.points_enabled) \
        .filter(EnabledFeatures.server_id == ctx.guild.id) \
        .one_or_none()
    if points_enabled is None or points_enabled[0]:
        if ctx.invoked_subcommand is None:
            await ctx.send(f'You need to provide a subcommand')
    else:
        # if feature is not enabled don't do anything
        ctx.invoked_subcommand = None


@points.command()
async def leaderboard(ctx, argument='team'):
    session = base.Session()
    if argument.lower() not in ('team', 'user'):
        await ctx.send(f'Please pick a valid choice - either team or user')
    else:
        if argument.lower() == 'team':
            board = session.query(Teams.name, Teams.point_total)\
                .filter(Teams.server_id == ctx.guild.id)\
                .order_by(Teams.point_total.desc())\
                .all()
        else:
            board = session.query(UserPoints.user_id, UserPoints.point_total)\
                .filter(UserPoints.server_id == ctx.guild.id)\
                .order_by(UserPoints.point_total.desc())\
                .all()
        if board is None:
            await ctx.send(f'Please award points or create teams first')
        else:
            await ctx.send(await util.pretty_print_leaderboard(board, ctx))


@points.group()
async def mod(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f'You need to provide a subcommand add or remove')


@mod.command()
async def add(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(f'You need to provide a server member')
    else:
        if ctx.guild.owner_id == ctx.author.id:
            session = base.Session()
            user = session.query(PrivilegedUsers.user_id)\
                .filter(PrivilegedUsers.server_id == ctx.guild.id)\
                .filter(PrivilegedUsers.user_id == member.id)\
                .one_or_none()
            if user is None:
                stmt = insert(PrivilegedUsers)\
                    .values(user_id=member.id, server_id=ctx.guild.id, allow_points=True)
                session.execute(stmt)
                session.commit()
                await ctx.send(f'{member.name} provided with point privileges')
            else:
                await ctx.send(f'{member.name} already has point privileges')
        else:
            await ctx.send(f'Only the server owner is allowed to assign point giver role')


@mod.command()
async def remove(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(f'You need to provide a server member')
    else:
        if ctx.guild.owner_id == ctx.author.id:
            session = base.Session()
            stmt = update(PrivilegedUsers)\
                .where(PrivilegedUsers.server_id == ctx.guild.id)\
                .where(PrivilegedUsers.user_id == member.id)\
                .values(allow_points=False)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Successfully removed {member.name} as point giver')
        else:
            await ctx.send(f'Only the server owner can remove point givers')


@points.group()
async def team(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f'You need to provide a subcommand - add - remove - award')


@team.command()
async def add(ctx, name, role: discord.Role):
    if ctx.guild.owner_id == ctx.author.id:
        session = base.Session()
        team_obj = session.query(Teams.team_id)\
            .filter(Teams.team_id == role.id)\
            .filter(Teams.server_id == ctx.guild.id)\
            .one_or_none()
        if team_obj is None:
            stmt = insert(Teams)\
                .values(team_id=role.id, server_id=ctx.guild.id, name=name, point_total=0)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Successfully created {name}')
        else:
            await ctx.send(f'A team using the role *{role.name}* already exists')
    else:
        await ctx.send(f'Only the server owner is allowed to create new teams')


@team.command()
async def remove(ctx, role: discord.Role):
    if ctx.guild.owner_id == ctx.author.id:
        session = base.Session()
        team_obj = session.query(Teams.name)\
            .filter(Teams.server_id == ctx.guild.id)\
            .filter(Teams.team_id == role.id)\
            .one_or_none()
        if team_obj is None:
            await ctx.send(f'Team using role {role.name} does not exist')
        else:
            stmt = delete(Teams)\
                .filter(Teams.server_id == ctx.guild.id)\
                .filter(Teams.team_id == role.id)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Successfully removed {team_obj[0]}')
    else:
        await ctx.send(f'Only the server owner is allowed to remove teams')


@team.command()
async def award(ctx, role: discord.Role, points_amount):
    session = base.Session()
    privileged = util.check_privilege(session=session, ctx=ctx, points=True, teams=False)
    if privileged is False and ctx.guild.owner_id != ctx.author.id:
        await ctx.send(f'You are not allowed to update points')
    else:
        message_content = util.update_team_total(session=session, ctx=ctx, points=points_amount, team_name=role.name,
                                                 team_id=role.id)
        await ctx.send(message_content)


@points.command()
async def award(ctx, member: discord.Member, points_amount):
    session = base.Session()
    privileged = util.check_privilege(session=session, ctx=ctx, points=True, teams=False)
    if privileged is False and ctx.guild.owner_id != ctx.author.id:
        await ctx.send(f'You are not allowed to update points')
    member_points_call = session.query(UserPoints.point_total, UserPoints.team_id)\
        .filter(UserPoints.server_id == ctx.guild.id)\
        .filter(UserPoints.user_id == member.id)\
        .one_or_none()
    if member_points_call is None:
        team_id_and_name = util.check_team(session=session, ctx=ctx, member=member)
        stmt = insert(UserPoints)\
            .values(user_id=member.id, team_id=team_id_and_name[0],
                    point_total=points_amount, server_id=ctx.guild.id)
        session.execute(stmt)
        session.commit()
        message_content = f'Added {points_amount} to {member.display_name} which is their new total'
        if team_id_and_name:
            session = base.Session()
            message_content = util.update_team_total(session=session, ctx=ctx, points=points_amount,
                                                     team_name=team_id_and_name[0][1], team_id=team_id_and_name[0][0],
                                                     message_content=message_content)
        await ctx.send(message_content)
    else:
        total = member_points_call[0] + int(points_amount)
        stmt = update(UserPoints)\
            .where(UserPoints.server_id == ctx.guild.id)\
            .where(UserPoints.user_id == member.id).values(point_total=total)
        session.execute(stmt)
        session.commit()
        message_content = f'Added {points_amount} to {member.display_name} their new total is {total}'

        if member_points_call[1] is not None:
            session = base.Session()
            team_id_and_name = util.check_team(session=session, ctx=ctx, member=member)
            if team_id_and_name:
                message_content = util.update_team_total(session=session, ctx=ctx, team_id=team_id_and_name[0][0],
                                                         team_name=team_id_and_name[0][1], points=points_amount,
                                                         message_content=message_content)
        await ctx.send(message_content)


@bot.group()
async def quote(ctx):
    session = base.Session()
    quote_enabled = session.query(EnabledFeatures.quotes_enabled) \
        .filter(EnabledFeatures.server_id == ctx.guild.id) \
        .one_or_none()
    if quote_enabled is None or quote_enabled[0]:
        if ctx.invoked_subcommand is None:
            await ctx.send(f'You need to provide a subcommand - add - remove - random - show')
    else:
        # if feature is not enabled don't do anything
        ctx.invoked_subcommand = None


@quote.command()
async def add(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(f'Please provide member to quote')
    else:
        quote_text = ctx.message.content
        length_removed = len(f'<@{member.id}>') + 12
        quote_text = quote_text[length_removed:]
        quote_text = quote_text.strip()
        if quote_text[0] in ('"', "'"):
            await ctx.send('Please try again without quotes')
        elif len(quote_text) < 1:
            await ctx.send(f'Please provide the quote with your command')
        else:
            session = base.Session()
            stmt = insert(Quote)\
                .values(server_id=ctx.guild.id, user_id=member.id,
                        quote_text=quote_text.strip(), date_quoted=date.today())
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Added quote to {member.name} - {quote_text.strip()}')


@quote.command()
async def remove(ctx, member: discord.Member = None, quote_id=None):
    if member is None or quote_id is None:
        await ctx.send(f'Please provide both member and quote id to use command')
    else:
        if ctx.author.id == member.id or ctx.guild.owner_id == ctx.author.id:
            session = base.Session()
            stmt = delete(Quote)\
                .filter(Quote.server_id == ctx.guild.id)\
                .filter(Quote.user_id == member.id)\
                .filter(Quote.quote_id == quote_id)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'If quote existed, it no longer does')
        else:
            await ctx.send(f'You can only remove quotes credited to you')


@quote.command()
async def random(ctx, member: discord.Member = None):
    session = base.Session()
    if member is None:
        quotes_total = util.quotes_server_total(session=session, ctx=ctx)
        if quotes_total > 0:
            quote_number = ran_num.randint(1, quotes_total)
            quote_formatted = await util.get_random_quote(session=session, quote_number=quote_number, ctx=ctx)
            await ctx.send(quote_formatted)
        else:
            await ctx.send(f'No quotes found for this server')
    else:
        quotes_total = util.quotes_by_user(session=session, ctx=ctx, member=member)
        if quotes_total > 0:
            quote_number = ran_num.randint(1, quotes_total)
            quote_formatted = await util.get_random_quote_member(session=session, quote_number=quote_number,
                                                                 ctx=ctx, member=member)
            await ctx.send(quote_formatted)
        else:
            await ctx.send(f'No quotes found for this server')


@quote.command()
async def show(ctx, member: discord.Member = None, command=None):
    if member is None or command is None:
        await ctx.send(f'Please provide both member and command to use this')
    else:
        session = base.Session()
        if command.isdigit():
            quote_displayed = session.query(Quote.quote_text, Quote.date_quoted)\
                .filter(Quote.server_id == ctx.guild.id)\
                .filter(Quote.user_id == member.id)\
                .filter(Quote.quote_id == int(command))\
                .one_or_none()
            if quote_displayed is not None:
                display_text = util.pretty_print_quote(member=member,
                                                       quote_text=quote_displayed[0],
                                                       quote_date=quote_displayed[1])
                print(display_text)
                await ctx.send(display_text)
            else:
                await ctx.send(f'No quote with id {command} exist for {member.name}')
        else:
            if command.lower() == 'all':
                quotes = session.query(Quote.quote_text, Quote.date_quoted, Quote.quote_id)\
                    .filter(Quote.server_id == ctx.guild.id)\
                    .filter(Quote.user_id == member.id)\
                    .all()
                output_text = ''
                for row in quotes:
                    output_text = output_text + 'ID: ' + str(row[2]) + ' ' \
                                  + util.pretty_print_quote(member=member, quote_text=row[0], quote_date=row[1]) + '\n'
                if output_text == '':
                    await ctx.send(f'No quotes found for this server')
                else:
                    await ctx.send(output_text)


bot.run(os.getenv('TOKEN', ''))
