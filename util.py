import discord
from discord.ext import commands

DEFAULT_ROLE_COLOR: discord.Color = discord.Color.blue()
CACHE_FILE = "cache.json"
LEAGUE_ID_KEY = {
    "AL": "Albany-Commodore",
    "ATL": "Atlanta-Marist",
    "COL": "Columbus-Muscogee",
    "DUG": "Douglasville",
    "EP": "Etowah-Paulding",
    "LEJ": "Lakeview-East Jackson",
    "MAC": "Macon-FPDS",
    "MW": "Marietta-Wheeler"
}
SEASON = "2025"
SEASONS = []
for season in range(2006, 2026):
    SEASONS.append(str(season))

async def is_valid_year(ctx: commands.Context, year: str, verbose: bool = True) -> bool:
    if not year.isdigit or len(year) != 4 or int(year) < 2006 or int(year) > int(SEASON):
        if verbose:
            await ctx.send("Invalid year.")
        return False
    return True

async def is_valid_team_number(ctx: commands.Context, team_number: str, verbose: bool = True) -> bool:
    if not team_number.isdigit() or len(team_number) > 5:
        if verbose:
            await ctx.send("Invalid team number.")
        return False
    return True

async def is_valid_league_id(ctx: commands.Context, league_id: str, verbose: bool = True) -> bool:
    if league_id.upper() not in LEAGUE_ID_KEY:
        if verbose:
            embed = Embed(
            title="Invalid league ID",
            description="See valid league IDs below",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Valid league IDs",
            value="\n".join([f"**{key}** - {value}" for key, value in LEAGUE_ID_KEY.items()]),
            inline=False
        )

        await embed.send(ctx)
        return False
    return True

async def get_role(ctx: commands.Context, role_name: str, verbose: bool = True) -> discord.Role | None:
    role: discord.Role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role and verbose:
        await ctx.send(f"The {role_name} role doesn't exist!")
        return None
    return role

async def create_role(ctx: commands.Context, role_name: str, color: discord.Color = DEFAULT_ROLE_COLOR) -> discord.Role:
    try:
        role: discord.Role = await ctx.guild.create_role(name=role_name, color=color)
        return role
    except discord.Forbidden:
        await ctx.send("I don't have permission to create roles.")
        return None

def check_user_has_role(ctx: commands.Context, role: discord.Role) -> bool:
    return role in ctx.author.roles

async def add_role_to_user(ctx: commands.Context, role: discord.Role, verbose: bool = True):
    try:
        await ctx.author.add_roles(role)
        if verbose:
            await ctx.send(f"You have been added to {role.name}!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to add roles.")

async def remove_role_from_user(ctx: commands.Context, role: discord.Role, verbose: bool = True):
    try:
        await ctx.author.remove_roles(role)
        if verbose:
            await ctx.send(f"You have been removed from {role.name}!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove roles.")

class Embed:
    embed: discord.Embed

    def __init__(self, title: str, description: str = "", color: discord.Color = DEFAULT_ROLE_COLOR):
        self.embed = discord.Embed(title=title, description=description, color=color)

    def add_field(self, name: str, value: str, inline: bool = False):
        self.embed.add_field(name=name, value=value, inline=inline)
    
    async def send(self, ctx: commands.Context):
        self.embed.set_footer(text="Requested by " + str(ctx.author.name))
        self.embed.timestamp = ctx.message.created_at
        await ctx.send(embed=self.embed)

class Team:
    number: str
    name: str
    sponsors: str
    school: str
    city: str
    state: str
    country: str
    website: str
    rookie_year: int
    location: str
    league: str

    def __init__(self, data: dict):
        self.number = str(data.get("teamNumber"))
        self.name = data.get("nameShort")
        self.sponsors = data.get("nameFull")
        self.school = data.get("schoolName")
        self.city = data.get("city")
        self.state = data.get("stateProv")
        self.country = data.get("country")
        self.website = data.get("website")
        self.rookie_year = data.get("rookieYear")
        self.location = data.get("displayLocation")
        self.league = data.get("league")

    def get_role(self, ctx: commands.Context) -> discord.Role:
        return discord.utils.get(ctx.guild.roles, name=self.number)
    
class Event:
    code: str
    name: str
    league: str
    type: str
    field_count: str
    venue: str
    city: str
    address: str
    website: str
    stream_url: str
    date_start: str
    date_end: str

    def __init__(self, data: dict):
        self.code = data.get("code")
        self.name = data.get("name")
        self.league = data.get("leagueCode")
        self.type = data.get("typeName")
        self.field_count = str(data.get("fieldCount"))
        self.venue = data.get("venue")
        self.city = data.get("city")
        self.address = data.get("address")
        self.website = data.get("website")
        self.stream_url = data.get("liveStreamUrl")
        self.date_start = data.get("dateStart")
        self.date_end = data.get("dateEnd")

class Ranking:
    rank: str
    team_number: str
    team_name: str
    ranking_score: str # sortOrder1
    avg_points_np: str # sortOrder2
    wins: str
    ties: str
    losses: str
    qual_avg: str
    dq: str
    matches_played: str
    matches_counted: str

    def __init__(self, data: dict):
        self.rank = str(data.get("rank"))
        self.team_number = data.get("displayTeamNumber")
        self.team_name = data.get("teamName")
        self.ranking_score = str(round(data.get("sortOrder1"), 1))
        self.avg_points_np = str(round(data.get("sortOrder2")))
        self.wins = str(data.get("wins"))
        self.ties = str(data.get("ties"))
        self.losses = str(data.get("losses"))
        self.qual_avg = str(data.get("qualAverage"))
        self.dq = str(data.get("dq"))
        self.matches_played = str(data.get("matchesPlayed"))
        self.matches_counted = str(data.get("matchesCounted"))

class Rankings:
    rankings: list[Ranking] = []

    def __init__(self, data: list[dict]):
        self.rankings = []
        for ranking in data:
            self.rankings.append(Ranking(ranking))

class Season:
    event_count: str
    game_name: str
    kickoff: str
    rookie_start: str
    team_count: str

    def __init__(self, data: dict):
        if data == None:
            return None
        self.event_count = str(data.get("eventCount"))
        self.game_name = data.get("gameName")
        self.kickoff = data.get("kickoff")
        self.rookie_start = str(data.get("rookieStart"))
        self.team_count = str(data.get("teamCount"))

class Cache:
    teams: list[Team]
    seasons: dict = {}
    events: list[Event]
    rankings: dict = {}
    timestamp: float

    def __init__(self, data: dict):
        self.teams = [Team(team) for team in data.get("teams", [])]

        for year, season in data.get("seasons", {}).items():
            self.seasons[year] = Season(season) if season else None

        self.events = [Event(event) for event in data.get("events", [])]

        for event in self.events:
            self.rankings[event.code] = Rankings(data.get("rankings", {}).get(event.code))
        
        self.timestamp = data.get("timestamp")