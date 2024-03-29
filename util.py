import discord
from PrivilegedUsers import PrivilegedUsers
from EnabledFeatures import EnabledFeatures
from Teams import Teams
from Quotes import Quote
from sqlalchemy import update, func, insert


def help_text():
    help_texty = f'help_me - shows this help text\n' \
                 f'setup prefix [prefix] - allows you to set a custom one character prefix default is ?\n' \
                 f'setup feature points [on/off] - enables or disables the points commands default is on\n' \
                 f'setup feature quotes [on/off] - enables or disables the quote commands default is on\n' \
                 f'points leaderboard - shows the current team standings optionally add users to get user ' \
                 f'leaderboard\n' \
                 f'points award [@member] [points] - gives points to server member and their team\n' \
                 f'points mod add [@member] - grant a server member rights to update points\n' \
                 f'points mod remove [@member] - revokes members rights to update points\n' \
                 f'points team add [name] [@role] - adds a team with the name given shadowing the given role\n' \
                 f'points team remove [@role] - removes team and points attached to the role\n' \
                 f'points team award [@role] [points] - gives points to team with the given role\n' \
                 f'joined [@member] - shows when the given member joined\n' \
                 f'quote add [@member] [quote] - adds a quote said by the member\n' \
                 f'quote remove [@member] [quote id] - removes a quote added to a member privileged users and the ' \
                 f'member quoted can remove it \n' \
                 f'quote random [@member] - shows a random quote by user or totally random quote if ' \
                 f'member isn\'t provided \n' \
                 f'quote show [@member] [quote id/all] - shows the members quote with the given id or all to list ' \
                 f'all with the quote id'
    return help_texty


async def pretty_print_leaderboard(board, ctx):
    row_no = 1
    board_list = ''
    for row in board:
        if isinstance(row[0], int):
            member = await ctx.guild.fetch_member(row[0])
            name = member.display_name
        else:
            name = row[0]
        board_list += f'{row_no}) {name} - {row[1]}\n'
        row_no += 1
    if board_list == "":
        return 'Leaderboard is empty!'
    return board_list


def enable_disable_feature(session, ctx, enabled, feature):
    if enabled not in ('on', 'off'):
        return f'Please provide either on or off to enable or disable feature'
    else:
        if ctx.guild.owner_id == ctx.author.id:
            if enabled == 'on':
                new_state = True
            else:
                new_state = False
            if feature == 'quote':
                stmt = session.query(EnabledFeatures.quotes_enabled)
                quote_state = new_state
                points_state = True
            elif feature == 'points':
                stmt = session.query(EnabledFeatures.points_enabled)
                points_state = new_state
                quote_state = True
            else:
                return f'Feature {feature} does\'t exist'
            feature_enabled = stmt.filter(EnabledFeatures.server_id == ctx.guild.id).one_or_none()
            if feature_enabled is None:
                stmt = insert(EnabledFeatures) \
                    .values(server_id=ctx.guild.id, quotes_enabled=quote_state, points_enabled=points_state)
                session.execute(stmt)
                session.commit()
            else:
                if feature_enabled == new_state:
                    return f'Feature is already {enabled}'
                else:
                    stmt = update(EnabledFeatures) \
                        .where(EnabledFeatures.server_id == ctx.guild.id)
                    if feature == 'points':
                        stmt = stmt.values(points_enabled=new_state)
                    elif feature == 'quote':
                        stmt = stmt.values(quotes_enabled=new_state)
                    session.execute(stmt)
                    session.commit()
                    return f'Feature is now {enabled}'
        else:
            return f'Only server owner can enable or disable features'


def check_privilege(session, ctx, points, teams):
    stmt = session.query(PrivilegedUsers.server_id)\
        .filter(PrivilegedUsers.server_id == ctx.guild.id)
    if points:
        stmt = stmt.filter(PrivilegedUsers.allow_points is True)
    if teams:
        stmt = stmt.filter(PrivilegedUsers.allow_teams is True)
    basic_stmt = stmt
    user = stmt.filter(PrivilegedUsers.user_id == ctx.author.id).one_or_none()
    if user is not None:
        return True
    role = basic_stmt.filter(PrivilegedUsers.role_id.in_([role.id for role in ctx.author.roles])).all()
    if role is not None:
        return True
    return False


def check_team(session, ctx, member: discord.Member):
    teams = session.query(Teams.team_id, Teams.name)\
        .filter(Teams.server_id == ctx.guild.id)\
        .filter(Teams.team_id.in_([role.id for role in member.roles]))\
        .all()
    if teams is None:
        return None
    else:
        return teams


def quotes_server_total(session, ctx):
    number_of_quotes = session.query(Quote.quote_id) \
        .filter(Quote.server_id == ctx.guild.id) \
        .count()
    return int(number_of_quotes)


def quotes_by_user(session, ctx, member: discord.Member):
    number_of_quotes = session.query(Quote.quote_id)\
        .filter(Quote.server_id == ctx.guild.id)\
        .filter(Quote.user_id == member.id)\
        .count()
    return int(number_of_quotes)


async def get_random_quote(session, ctx, quote_number):
    quotes_from_server = session.query(Quote.quote_text, Quote.user_id, Quote.date_quoted)\
        .filter(Quote.server_id == ctx.guild.id)\
        .limit(1)\
        .offset(quote_number - 1)\
        .all()
    member = await ctx.guild.fetch_member(quotes_from_server[0][1])
    return pretty_print_quote(member=member, quote_text=quotes_from_server[0][0], quote_date=quotes_from_server[0][2])


def pretty_print_quote(member: discord.Member, quote_text, quote_date):
    return f'"{quote_text.capitalize()}" - *{member.name}, {quote_date}*'


def update_team_total(session, ctx, team_id, team_name, points, message_content=''):
    team_points = session.query(Teams.point_total, Teams.name) \
        .filter(Teams.server_id == ctx.guild.id) \
        .filter(Teams.team_id == team_id) \
        .one_or_none()
    if team_points is None:
        message_content = (message_content + '\n' + f'No team related to {team_name} exists on this server')
    else:
        if team_points[0] is None:
            starting_points = 0
        else:
            starting_points = team_points[0]
        point_total = starting_points + int(points)
        stmt = update(Teams) \
            .where(Teams.server_id == ctx.guild.id) \
            .where(Teams.team_id == team_id) \
            .values(point_total=point_total)
        session.execute(stmt)
        session.commit()
        message_content = (message_content + '\n' + f'Successfully updated {team_points[1]}s points by {points} - '
                                                    f'New point total is {point_total}')
    return message_content


async def get_random_quote_member(session, quote_number, ctx, member):
    quotes_from_server = session.query(Quote.quote_text, Quote.user_id, Quote.date_quoted) \
        .filter(Quote.server_id == ctx.guild.id)\
        .filter(Quote.user_id == member.id) \
        .limit(1) \
        .offset(quote_number - 1) \
        .all()
    member = await ctx.guild.fetch_member(quotes_from_server[0][1])
    return pretty_print_quote(member=member, quote_text=quotes_from_server[0][0], quote_date=quotes_from_server[0][2])

