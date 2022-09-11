import discord
from discord.ext import commands
import base
from PrivilegedUsers import PrivilegedUsers
from Teams import Teams
from UserPoints import UserPoints
from CustomChanges import CustomChanges
import os
from dotenv import load_dotenv
from sqlalchemy import insert, delete, update
import util

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
        prefix = '£'
    return prefix


bot = commands.Bot(command_prefix=custom_prefix, description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


# TODO help command
@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')


@bot.command()
async def set_prefix(ctx, alias):
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
            .set(command_prefix=alias)
    session.execute(stmt)
    session.commit()
    await ctx.send(f'New command prefix is now {alias}')


@bot.command()
async def point_giver(ctx, member: discord.Member):
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


@bot.command()
async def add_team(ctx, name, role: discord.Role):
    if ctx.guild.owner_id == ctx.author.id:
        session = base.Session()
        team = session.query(Teams.team_id)\
            .filter(Teams.team_id == role.id)\
            .filter(Teams.server_id == ctx.guild.id)\
            .one_or_none()
        if team is None:
            stmt = insert(Teams)\
                .values(team_id=role.id, server_id=ctx.guild.id, name=name, point_total=0)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Successfully created {name}')
        else:
            await ctx.send(f'A team using the role *{role.name}* already exists')
    else:
        await ctx.send(f'Only the server owner is allowed to create new teams')


@bot.command()
async def remove_team(ctx, role: discord.Role):
    if ctx.guild.owner_id == ctx.author.id:
        session = base.Session()
        team = session.query(Teams.name)\
            .filter(Teams.server_id == ctx.guild.id)\
            .filter(Teams.team_id == role.id)\
            .one_or_none()
        if team is None:
            await ctx.send(f'Team using role {role.name} does not exist')
        else:
            stmt = delete(Teams)\
                .filter(Teams.server_id == ctx.guild.id)\
                .filter(Teams.team_id == role.id)
            session.execute(stmt)
            session.commit()
            await ctx.send(f'Successfully removed {team[0]}')
    else:
        await ctx.send(f'Only the server owner is allowed to remove teams')


@bot.command()
async def leaderboard(ctx, argument='team'):
    session = base.Session()
    if argument.lower() not in ('team', 'user'):
        await ctx.send(f'Please pick a valid choice')
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


@bot.command()
async def individual_points(ctx, member: discord.Member, points):
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
                    point_total=points, server_id=ctx.guild.id)
        session.execute(stmt)
        session.commit()
        message_content = f'Added {points} to {member.display_name} which is their new total'
        if team_id_and_name is not None:
            session = base.Session()
            message_content = util.update_team_total(session=session, ctx=ctx, points=points,
                                                     team_name=team_id_and_name[0][1], team_id=team_id_and_name[0][0],
                                                     message_content=message_content)
        await ctx.send(message_content)
    else:
        total = member_points_call[0] + int(points)
        stmt = update(UserPoints)\
            .where(UserPoints.server_id == ctx.guild.id)\
            .where(UserPoints.user_id == member.id).values(point_total=total)
        session.execute(stmt)
        session.commit()
        message_content = f'Added {points} to {member.display_name} their new total is {total}'

        if member_points_call[1] is not None:
            session = base.Session()
            team_id_and_name = util.check_team(session=session, ctx=ctx, member=member)
            message_content = util.update_team_total(session=session, ctx=ctx, team_id=team_id_and_name[0][0],
                                                     team_name=team_id_and_name[0][1], points=points,
                                                     message_content=message_content)
        await ctx.send(message_content)


@bot.command()
async def update_points(ctx, role: discord.Role, points):
    session = base.Session()
    privileged = util.check_privilege(session=session, ctx=ctx, points=True, teams=False)
    if privileged is False and ctx.guild.owner_id != ctx.author.id:
        await ctx.send(f'You are not allowed to update points')
    else:
        message_content = util.update_team_total(session=session, ctx=ctx, points=points, team_name=role.name, team_id=role.id)
        await ctx.send(message_content)


bot.run(os.getenv('TOKEN', ''))
