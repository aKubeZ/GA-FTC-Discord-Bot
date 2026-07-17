import math
import random
import numbers

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import re

import numpy

import api
import data
import util
import calculator
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def feed_and_say(input, message: discord.Message):
    markov.feed(input)
    await message.reply(markov.gen_response(), mention_author=False)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.listen('on_message')
async def message_listener(message: discord.Message):
    # message.
    if message.reference and message.reference.resolved and bot.application_id == message.reference.resolved.author.id:
        await feed_and_say(message.content, message)

@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f"Welcome to the server, {member.mention}, run `!join <team_number>` in #bot-commands to join your team and league")

@bot.hybrid_command(name="ping", description="Check the bot's latency")
async def ping(ctx: commands.Context):
    '''Check the bot's latency and respond with "Pong!" and the latency in milliseconds.'''
    await ctx.send(f"Pong! (in {round(bot.latency * 1000)}ms)")

# region FTC Commands

@bot.hybrid_command(name="join", description="Add yourself to a team")
async def join(ctx: commands.Context, team_number: str):
    '''
    Add yourself to a team. If the team doesn't have a role in the server, it will be created.
    
    Args:
        team_number (str): The number of the team to join as a string.
    '''
    team_info: util.Team = await data.get_team(ctx, team_number, verbose=False)
    if not team_info:
        await ctx.send(f"Team {team_number} not found.")
        return
    
    role: discord.Role = await util.get_role(ctx, team_number, verbose=False)
    if not role:
        role = await util.create_role(ctx, team_number)
        if not role:
            return

        # Sort roles by position lowest-to-highest to find the bottom one first
        lowest_numeric_role = None
        for r in sorted(ctx.guild.roles, key=lambda x: x.position):
            if r.name.isdigit() and r.name != str(team_number):
                lowest_numeric_role = r
                break

        if lowest_numeric_role is not None:
            print(f"Moving role {role.name} to position below {lowest_numeric_role.name}")
            await role.edit(position=lowest_numeric_role.position - 1)

        if role:
            await ctx.send(f"Created role for team {team_number}, use `!set_color {team_number} #ffffff` to change the role color with a custom hex code.")
        else:
            await ctx.send(f"Failed to create role for team {team_number}.")
            return

    if util.check_user_has_role(ctx, role):
        await ctx.send(f"You are already on team {team_number}!")
        return

    await util.add_role_to_user(ctx, role, verbose=False)
    league_role: discord.Role = await util.get_role(ctx, util.LEAGUE_ID_KEY.get(team_info.league))
    await util.add_role_to_user(ctx, league_role, verbose=False)
    await ctx.send(f"You have been added to team {team_number} and the {util.LEAGUE_ID_KEY.get(team_info.league)} league!")
    return

@bot.hybrid_command(name="leave", description="Remove yourself from a team")
async def leave(ctx: commands.Context, team_number: str):
    '''
    Remove yourself from a team. You must be on the team to leave it.

    Args:
        team_number (str): The number of the team to leave as a string.
    '''
    team_info: util.Team = await data.get_team(ctx, team_number, verbose=False)
    if not team_info:
        await ctx.send(f"Team {team_number} not found.")
        return

    role: discord.Role = await util.get_role(ctx, team_number)
    if not role: return

    if not util.check_user_has_role(ctx, role):
        await ctx.send(f"You aren't on team {team_number}!")
        return
    
    await util.remove_role_from_user(ctx, role, verbose=False)
    league_role: discord.Role = await util.get_role(ctx, util.LEAGUE_ID_KEY.get(team_info.league))
    if league_role: 
        await util.remove_role_from_user(ctx, league_role, verbose=False)
    await ctx.send(f"You have been removed from team {team_number} and the {util.LEAGUE_ID_KEY.get(team_info.league)} league!")

    if not role.members:
        try:
            await role.delete()
            await ctx.send(f"Role for team {team_number} has been deleted as it has no members.")
        except discord.Forbidden:
            await ctx.send(f"Role for team {team_number} has no members but I don't have permission to delete it.")

    return

@bot.hybrid_command(name="set_color", description="Set the color of a team role")
async def set_color(ctx: commands.Context, team_number: str, color_hex: str):
    '''
    Set the color of a team role. You must be on the team to change its color.

    Args:
        team_number (str): The number of the team to change the color of as a string.
        color_hex (str): The hex code of the color to set the role to, e.g. "#ff0000".
    '''
    role: discord.Role = await util.get_role(ctx, team_number)
    if not role: return

    if not util.check_user_has_role(ctx, role) and not ctx.author.guild_permissions.administrator:
        await ctx.send(f"You aren't on team {team_number}!")
        return

    try:
        color = discord.Color(int(color_hex.lstrip("#"), 16))
    except ValueError:
        await ctx.send(f"{color_hex} is not a valid hex code.")
        return

    try:
        await role.edit(color=color)
        await ctx.send(f"Role for team {team_number} has been updated to {color_hex}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change the role color.")

@bot.hybrid_command(name="members", description="List members of a team")
async def members(ctx: commands.Context, team_number: str):
    '''
    List members of a team, including alumni. If the team has a role in the server, 
    the embed will be colored to match the role's color.

    Args:
        team_number (str): The number of the team to list members for as a string.
    '''
    role: discord.Role = await util.get_role(ctx, team_number)
    if not role: return
    alum_role: discord.Role = await util.get_role(ctx, "Alumni")
    if not alum_role: return

    members = []
    alumni_members = []
    for member in role.members:
        member_string = f"**{member.display_name}** ({member.name})".replace("||", "|") # Prevent spoilers
        if alum_role not in member.roles:
            members.append(member_string)
        else:
            alumni_members.append(member_string)

    if not members and not alumni_members:
        await ctx.send(f"No members found on team {team_number}.")
        return

    embed = util.Embed(
        title=f"Team {team_number}",
        description=f"{len(members)} member(s) and {len(alumni_members)} alumni found",
        color=role.color
    )

    if members:
        embed.add_field(name="Members:", value="\n".join(members))
        
    if alumni_members:
        embed.add_field(name="Alumni:", value="\n".join(alumni_members))

    await embed.send(ctx)

@bot.hybrid_command(name="team", description="Show information about a team")
async def team(ctx: commands.Context, team_number: str):
    '''
    Show information about a team, including its name, location, league, website, rookie year, and sponsors.
    If the team has a role in the server, the embed will be colored to match the role's color.

    Args:
        team_number (str): The number of the team to show information about as a string.
    '''
    team: util.Team = await data.get_team(ctx, team_number)
    if not team:
        await ctx.send(f"Team {team_number} not found.")
        return
    
    role: discord.Role = await util.get_role(ctx, team.number, verbose=False) # May or may not exist
    embed = util.Embed(
        title=f"Team {team_number}",
        description=team.name,
        color=role.color if role else util.DEFAULT_ROLE_COLOR
    )
    
    embed.add_field(name="Location", value=team.location)
    embed.add_field(name="League", value=util.LEAGUE_ID_KEY.get(team.league, "League not available."))
    embed.add_field(name="Website", value=team.website)
    embed.add_field(name="Rookie Year", value=team.rookie_year)
    embed.add_field(name="Sponsors", value=team.sponsors)
    embed.add_field(name="Members", value=f"Use `!members {team.number}` to see a list of team members.")
    embed.add_field(name="Event Web:", value=f"https://ftc-events.firstinspires.org/{util.SEASON}/team/{team.number}")
    embed.add_field(name="FTCScout:", value=f"https://ftcscout.com/team/{team.number}")
    await embed.send(ctx)

@bot.hybrid_command(name="leagues", description="Shows the leagues and their IDs")
async def leagues(ctx: commands.Context):
    '''
    Show the leagues and their IDs. This is useful for finding the league ID to use with the `!league` command.
    '''
    embed = util.Embed(
        title="Leagues",
        description="See leagues and their IDs below.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="League List",
        value="\n".join([f"**{key}** - {value}" for key, value in util.LEAGUE_ID_KEY.items()]),
        inline=False
    )
    embed.add_field(
        name="Specific Leagues",
        value="Use `!league <league_id>` to see the teams in a specific league.",
    )
    await embed.send(ctx)

@bot.hybrid_command(name="league", description="Shows the teams in a league")
async def league(ctx: commands.Context, league_id: str):
    '''
    Show the teams in a league, including their team numbers and names.

    Args:
        league_id (str): The ID of the league to show teams for as a string.
    '''
    if not await util.is_valid_league_id(ctx, league_id): 
        return

    teams = data.get_teams_in_league(league_id.upper())
    if not teams:
        await ctx.send(f"No teams found in league {league_id.upper()}.")
        return
    
    embed = util.Embed(
        title=f"{util.LEAGUE_ID_KEY[league_id.upper()]} League ({league_id.upper()})",
        description=f"{len(teams)} team(s) found in this league."
    )

    embed.add_field(
        name="Teams:", 
        value="\n".join([f"**{team.number}** - {team.name}" for team in teams]), 
    )

    embed.add_field("Event Web:", value=f"https://ftc-events.firstinspires.org/{util.SEASON}/region/USGA/league/{league_id.upper()}")

    await embed.send(ctx)

@bot.hybrid_command(name="season_data", description="seasons the data")
async def season_data(ctx: commands.Context, year: str):
    '''
    seasons the data
    '''
    
    season: util.Season = await data.get_season(ctx, year, verbose=False) # Can be null
    if not season:
        await ctx.send(f"Season {year} not found.")
        return
    
    embed = util.Embed(
        title=f"{year} Season",
        description=season.game_name
    )

    embed.add_field(name="Event Count", value=season.event_count)
    embed.add_field(name="Team Count", value=season.team_count)
    embed.add_field(name="Kickoff", value=season.kickoff)
    embed.add_field(name="Rookie Start", value=season.rookie_start)
    await embed.send(ctx)

@bot.hybrid_command(name="event", description="Gets event info")
async def event(ctx: commands.Context, event_code: str):
    '''
    Gets event info
    '''
    event_code = event_code.upper()
    event: util.Event = await data.get_event(ctx, event_code, verbose=False) # Can be null
    if not event:
        await ctx.send(f"Event {event_code} not found.")
        return
    
    embed = util.Embed(
        title=f"Event {event_code}",
        description=f"{event.name}"
    )

    embed.add_field(name="League", value=event.league)
    embed.add_field(name="Type", value=event.type)
    embed.add_field(name="Field Count", value=event.field_count)
    embed.add_field(name="Venue", value=event.venue)
    embed.add_field(name="City", value=event.city)
    embed.add_field(name="Address", value=event.address)
    embed.add_field(name="Website", value=event.website if event.website and event.website != "" else "Not Available")
    embed.add_field(name="Stream URL", value=event.stream_url if event.stream_url and event.stream_url != "" else "Not Available")
    embed.add_field(name="Start Date", value=event.date_start)
    embed.add_field(name="End Date", value=event.date_end)
    await embed.send(ctx)

@bot.hybrid_command(name="events", description="Lists event codes")
async def events(ctx: commands.Context):
    '''
    Lists event codes
    '''
    
    embed = util.Embed(
        title=f"Georgia FTC Event Codes"
    )

    events_list: str = "- "
    prev_league: str = ""
    for i, event in enumerate(data.cache.events):
        league: str = re.search(r'USGA([A-Z]*)(?:M1|M2|M3|M4|M5|M6|M7|LT|KO|OS)|USGA(CMP)', event.code).group(1)
        if i == 0:
            events_list += event.code
            prev_league = league
            continue
        if prev_league != league:
            events_list += "\n- "
        else:
            events_list += ", "
        events_list += event.code
        prev_league = league

    embed.add_field(
        name="Events List",
        value=events_list
    )

    embed.add_field(
        name="Specific Events",
        value="Use `!event <event_id>` to see info about the event"
    )
    await embed.send(ctx)

@bot.hybrid_command(name="rankings", description="Gets rankings of an event")
async def rankings(ctx: commands.Context, event_code: str, page_num = 1):
    '''
    Gets rankings of an event. (League meets have the same stats)
    RS = Ranking Score
    PTS = Average Points (without penalties)
    QA = Qualification Average
    DQ = i actually dont know what this means its just called 'dq' in the docs
    MP = Matches Played
    MC = Matches Counted
    '''
    event_code = event_code.upper()
    if event_code[:4] != "USGA":
        event_code = "USGA" + event_code
    rankings: util.Rankings = await data.get_rankings(ctx, event_code, verbose=False) # Can be null

    if not rankings:
        await ctx.send(f"Event {event_code} not found.")
        return
    
    max_page = math.ceil(len(rankings.rankings) / 10)
    if page_num > max_page or page_num <= 0:
        await ctx.send("Invalid page number.")
        return

    rankings_str: str = "# - Team — W-T-L — RS - PTS-QA-DQ—MP-MC\n"
    # rank - team num — w-t-l — rankingscore avgpoints qualavg dq — matchesplayed matchescounted
    
    for i in range(max(0, page_num * 10 - 10), min(len(rankings.rankings), page_num * 10)):
        ranking: util.Ranking = rankings.rankings[i]
        if len(rankings_str) >= 900: # discord has a 1024 char limit on embeds
            rankings_str += "...\n"
            break
        rankings_str += f"{ranking.rank} - **{ranking.team_number}** — {ranking.wins}-{ranking.ties}-{ranking.losses} —"\
            + f" {ranking.ranking_score} - {ranking.avg_points_np} - {ranking.qual_avg} - {ranking.dq} — "\
            + f"{ranking.matches_played} - {ranking.matches_counted}" + "\n"
    rankings_str = rankings_str[:-1]

    embed = util.Embed(
        title=f"Event {event_code} Rankings",
        description=f"Event Rankings"
    )

    embed.add_field(name=f"Event Rankings ({page_num}/{max_page})", value=rankings_str)
    await embed.send(ctx)

# endregion

# region Self Roles

@bot.hybrid_command(name="graduate", description="Mark yourself as an alumni")
async def graduate(ctx: commands.Context):
    '''
    Mark yourself as an alumni. This will add the "Alumni" role to your account.
    '''
    await util.add_role_to_user(ctx, await util.get_role(ctx, "Alumni"), verbose=False)
    await ctx.send("You are now an alumni! You can remove this role with `!ungraduate`.")

@bot.hybrid_command(name="ungraduate", description="Remove yourself as an alumni")
async def ungraduate(ctx: commands.Context):
    '''
    Remove yourself as an alumni. This will remove the "Alumni" role from your account.
    '''
    await util.remove_role_from_user(ctx, await util.get_role(ctx, "Alumni"), verbose=False)
    await ctx.send("You are no longer an alumni! You can add this role back with `!graduate`.")

@bot.hybrid_command(name="im_hungry", description="Get the hungry role for food notifications")
async def im_hungry(ctx: commands.Context):
    '''Get the hungry role.'''
    await util.add_role_to_user(ctx, await util.get_role(ctx, "Hungry"), verbose=False)
    await ctx.send("You are now hungry! You can remove this role with `!im_not_hungry`.")

@bot.hybrid_command(name="im_not_hungry", description="Remove the hungry role for food notifications")
async def unhungry(ctx: commands.Context):
    '''Remove the hungry role.'''
    await util.remove_role_from_user(ctx, await util.get_role(ctx, "Hungry"), verbose=False)
    await ctx.send("You are no longer hungry! You can add this role back with `!im_hungry`.")

# endregion

# region Calculator Stuff

calc_vars: dict = {}
def format_input(input):
    if input[0] == '`' and input[-1] == '`':
        return input[1:-1]
    else:
        return input

def format_output(output, precision=10, matrix_precision=2, left_indent=0, compact=False):
    # tuple case
    if isinstance(output, tuple):
        out_string = ""
        for i, indiv_output in enumerate(output):
            out_string += format_output(indiv_output, precision=precision, matrix_precision=matrix_precision, left_indent=(left_indent if i == 0 else 0))
            if i != len(output) - 1:
                out_string += ", "
                if not isinstance(indiv_output, numbers.Number):
                    out_string += "\n"

        return out_string
    # matrix case
    if isinstance(output, calculator.Matrix):
        rows = [[format_output(output.get(i, j), precision=matrix_precision, compact=True) for j in range(1, output.n + 1)] for i in range(1, output.m + 1)]
        max_lens = [max([len(rows[j][i]) for j in range(len(rows))]) for i in range(len(rows[0]))]
        row_strings = []
        # ⎡a b c⎤
        # ⎢d e f⎥
        # ⎣g h i⎦
        for i, row in enumerate(rows):
            row_string = (" " * left_indent if i != 0 else "") + ("[" if len(rows) == 1 else "⎡" if i == 0 else "⎢" if i != len(rows) - 1 else "⎣")
            for j, entry in enumerate(row):
                max_len = max_lens[j]
                entry_len = len(entry)
                half_net_padding = (max_len - entry_len) / 2
                left_padding = " " * math.ceil(half_net_padding)
                right_padding = " " * math.floor(half_net_padding)
                entry_string = left_padding + entry + right_padding
                if j != len(row) - 1:
                    entry_string += " "
                row_string += entry_string
            row_string += "]" if len(rows) == 1 else "⎤" if i == 0 else "⎥" if i != len(rows) - 1 else "⎦"
            row_strings.append(row_string)
        return "\n".join(row_strings)
    # vector case
    if isinstance(output, calculator.Vector): return format_output(calculator.Matrix(output), matrix_precision=matrix_precision, left_indent=left_indent)
    # complex case
    if numpy.iscomplex(output):
        out_real = round(output.real, precision)
        out_imag = round(output.imag, precision)
        if abs(out_real) <= 0.000000000000001:
            if abs(out_imag) <= 0.000000000000001: return "0"
            if out_imag == 1: return "i"
            if out_imag == -1: return "-i"
            return f"{format_output(out_imag)}i"
        elif abs(out_imag) <= 0.000000000000001:
            return format_output(out_real)
        else:
            return f"{format_output(out_real)}{"" if compact else " "}{"+" if out_imag >= 0 else "-"}{"" if compact else " "}{"" if abs(out_imag) == 1 else format_output(abs(out_imag))}i"
    # real case
    if round(abs(output), precision) <= 0.000000000000001: return "0"
    output = str(round(output.real, precision))
    output = re.sub(r'e\+?(-?[0-9]+)', r'×10^(\1)', output)
    output = re.sub(r'-0([0-9])', r'-\1', output)
    if output[-2:] == '.0': output = output[:-2]
    return output

@bot.hybrid_command(name="calc", description="""
                    Basic calculator that supports:
                    +, -, *, /, % (mod), ^, !, ln, exp, sqrt, cbrt, sign, sgn, abs, conj, hyp,
                    eye, zeros, ones, det, trace, tr, rref, T, transpose, & (cross product),
                    literally every trig func + hyperbolic trig func,
                    And constants e and pi.
                    To define a (column) vector:
                        <1, 2, 3>
                    To define a matrix:
                        Per row: [1, 2, 3; 4, 5, 6; 7, 8, 9]
                        Per column: [<1, 2, 3>, <4, 5, 6>, <7, 8, 9>]
                    """)
async def calc(ctx: commands.Context, *, input: str):
    '''Basic calculator.'''
    out = calculator.calculate(format_input(input), calc_vars)
    if out == calculator.syntax_error:
        await ctx.send("Syntax Error.")
        return
    if out == calculator.math_error:
        await ctx.send("Math Error.")
        return
    await ctx.send(f"```\n{format_output(out)}\n```")

@bot.hybrid_command(name="calca", description="""
                    Assigns value to the calculator memory.
                    Try !calca x 3
                    and !calc 3x+2
                    """)
async def calca(ctx: commands.Context, var: str, *, input: str):
    '''Assigns Values to the calculator memory'''
    out = calculator.calculate(format_input(input), calc_vars)
    if out == calculator.syntax_error:
        await ctx.send("Syntax Error.")
        return
    if out == calculator.math_error:
        await ctx.send("Math Error.")
        return
    calc_vars[var] = out
    await ctx.send(f"```\n{var} ← {format_output(out, left_indent=(len(var) + 3))}\n```")

@bot.hybrid_command(name="calcm", description="Sends the calculator memory")
async def calcm(ctx: commands.Context):
    '''Sends the calculator memory'''
    memory_string = ""
    if calc_vars == {}:
        await ctx.send("Nothing in memory.")
        return
    for variable, value in calc_vars.items():
        memory_string += f"{variable}: {format_output(value, left_indent=(2 + len(variable)))}\n"
    if len(memory_string) >= 2000:
        await ctx.send("Too many variables to display! Clear it please")
        return
    await ctx.send(f"```\n{memory_string}```")

@bot.hybrid_command(name="calcmc", description="Clears the calculator memory")
async def calcmc(ctx: commands.Context):
    '''Clears the calculator memory'''
    calc_vars.clear()
    await ctx.send("Calculator Memory Cleared.")

# endregion

answers: list[str] = ["yes definitely", "no dont pls dont", "what does that even mean??? ask chatgpt or something", "timmy says yes", "say that again i couldn't hear", "YES", "NO", "hell yeah", "ah hell no", "no.", "67"]
# answers: list[str] = ["yaaaaa"]
@bot.hybrid_command(name="tim", description="Ask me a yes or no question")
async def tim(ctx: commands.Context):
    '''Respond with a variant of yes or no.'''
    await ctx.send(answers[random.randrange(len(answers))])

import markov
@bot.hybrid_command(name="say", description="Ask me lit anything, !sayclear if i went rogue")
async def say(ctx: commands.Context, *, input: str):
    '''Responds with wtv, !sayclear if i went rogue'''
    await feed_and_say(input, ctx.message)

@bot.hybrid_command(name="sayclear", description="Reset my memory")
async def sayclear(ctx: commands.Context):
    '''use if !say spits out some vile stuff'''
    print(markov.words_data)
    markov.clear_response()

@bot.hybrid_command(name="echo", description="Repeats arguments")
async def echo(ctx: commands.Context, *, text: str):
    '''Echoes'''
    await ctx.send(text)

@bot.hybrid_command(name="kill", description="kill")
async def kill(ctx: commands.Context, *, usr: str):
    '''kill'''
    text: str = usr.lower()
    if text == "tim":
        mod = discord.utils.find(lambda r: r.name == 'Mod', ctx.message.guild.roles)
        if mod in ctx.author.roles:
            await ctx.message.add_reaction("💔")
            await ctx.send("WHAT DID I DOOO")
            quit()
        else:
            await ctx.message.add_reaction("🥀")
            await ctx.send("what are you trying to do sonion")
            return
    if "akube" in text or "ethan" in text or "840396811596464130" in text:
        await ctx.send("coulndt kill them mb :<")
    else:
        await ctx.send(f"killed {usr} [:3](https://cdn.discordapp.com/attachments/1368475349934936195/1461135751092768831/attachment.gif?ex=6a4e3075&is=6a4cdef5&hm=800297222d8511fe7191386e3613c7f383c342959fe368ec4da8bf5f935d0c1e)")

# region Mod Commands

@bot.hybrid_command(name="sync_leagues", description="Add people with existing team roles to their league roles", hidden=True)
@commands.has_role("Mod")
async def sync_leagues(ctx: commands.Context):
    '''
    Add people with existing team roles to their league roles. This is useful if the bot was added to a server
    that already has team roles and members.
    '''
    message: discord.Message = await ctx.send("Syncing leagues...")
    guild: discord.Guild = ctx.guild
    count = 0
    for role in guild.roles:
        if role.name.isdigit():
            team_info: util.Team = await data.get_team(ctx, role.name, verbose=False)
            if not team_info:
                continue
            league_role: discord.Role = await util.get_role(ctx, util.LEAGUE_ID_KEY.get(team_info.league), verbose=False)
            if not league_role:
                continue
            for member in role.members:
                if league_role not in member.roles:
                    try:
                        await member.add_roles(league_role)
                        print(f"Added {member.display_name} to {league_role.name} for being on team {role.name}.")
                        count += 1
                    except discord.Forbidden:
                        print(f"Failed to add {member.display_name} to {league_role.name} for being on team {role.name}.")
    await message.edit(content=f"Synced leagues successfully! Added {count} member(s) to their league roles.")

@bot.hybrid_command(name="add_role", description="Add a role to a user", hidden=True)
@commands.has_role("Mod")
async def add_role(ctx: commands.Context, user: discord.Member, role_name: str):
    '''
    Add a role to a user. This is useful for adding roles to users who are not on a team.

    Args:
        user (discord.Member): The user to add the role to.
        role_name (str): The name of the role to add.
    '''
    role: discord.Role = await util.get_role(ctx, role_name, verbose=False)
    if not role:
        await ctx.send(f"Role {role_name} not found.")
        return
    try:
        await user.add_roles(role)
        await ctx.send(f"Added {role.name} to {user.display_name}.")
    except discord.Forbidden:
        await ctx.send(f"Failed to add {role.name} to {user.display_name}. I don't have permission to do that.")

@bot.hybrid_command(name="sync", description="Force data sync", hidden=True)
@commands.has_role("Mod")
async def force_sync(ctx: commands.Context):
    try:
        message = await ctx.send("Fetching data...")
        data.load_cache(force_sync=True)
        await message.edit(content="Data sync complete!")
    except Exception as e:
        await ctx.send(f"Data sync failed: {e}")

@bot.hybrid_command(name="sync_commands", description="Sync slash commands", hidden=True)
@commands.has_role("Mod")
async def sync(ctx: commands.Context):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"Successfully synced {len(synced)} command(s) globally.")
    except Exception as e:
        await ctx.send(f"Failed to sync commands: {e}")

# endregion

if __name__ == "__main__":
    load_dotenv(".env") # Load environment variables from .env file

    api.init()
    data.load_cache(force_sync=False)

    bot.run(os.getenv("BOT_TOKEN"))