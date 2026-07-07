from discord.ext import commands
import json
import time
import os

import api
import util

cache: util.Cache = util.Cache({})

# region Data handlers
async def get_team(ctx: commands.Context, team_number: str, verbose: bool = True) -> util.Team | None:
    '''Returns the team info for the given team number from the cache. Returns None if not found.'''
    if not await util.is_valid_team_number(ctx, team_number, verbose=verbose):
        return None
    
    for team in cache.teams:
        if team.number == team_number:
            return team

    return None

async def get_event(ctx: commands.Context, event_code: str, verbose: bool = True) -> util.Team | None:
    '''Returns the event info for the given event code from the cache. Returns None if not found.'''
    
    for event in cache.events:
        if event.code == event_code:
            return event

    return None

async def get_season(ctx: commands.Context, year: str, verbose: bool = True) -> util.Season | None:
    '''Returns the season info for a given year from the cache. Returns None if not found.'''
    if not await util.is_valid_year(ctx, year, verbose=verbose):
        return None
    
    return cache.seasons.get(year)

async def get_rankings(ctx: commands.Context, event_code: str, verbose: bool = True) -> util.Rankings | None:
    '''Returns the rankings of an event'''
    
    return cache.rankings.get(event_code)

def get_teams_in_league(league_id: str) -> list[util.Team]:
    '''Returns a list of teams in the given league ID from the cache'''
    teams_in_league: list[util.Team] = []
    for team in cache.teams:
        if team.league == league_id:
            teams_in_league.append(team)

    return teams_in_league
# endregion

# region Load and sync
def load_cache(force_sync: bool = False) -> None:
    '''Loads cache into memory from the cache file'''
    global cache
    if not os.path.exists(util.CACHE_FILE) or force_sync:
        sync_cache()

    with open(util.CACHE_FILE, "r") as f:
        cache = util.Cache(json.load(f))
        f.close()
    
    return None

def sync_cache() -> None:
    '''Fetches new data from the API and updates the cache file'''
    print("Syncing cache...")

    with open(util.CACHE_FILE, "w") as f:
        teams: list[dict] = api.get_teams()["teams"]

        # Assign league IDs to teams based on the league membership data
        # Because it isn't given in the team data for some reason...
        for league_id in util.LEAGUE_ID_KEY.keys():
            league_teams: list[int] = api.get_league_teams(league_id)
            for league_team in league_teams:
                for team in teams:
                    if team["teamNumber"] == league_team:
                        team["league"] = league_id
        
        seasons: dict = {}

        for year in util.SEASONS:
            season: dict = api.get_season(year)
            if season:
                del season['fRCChampionships'] 
            seasons[year] = season

        events: list[dict] = api.get_events()

        rankings: dict = {}
        for event in events:
            rankings[event.get("code")] = api.get_rankings(event.get("code"))

        cache_data = {
            "teams": teams,
            "timestamp": time.time(),
            "seasons": seasons,
            "events": events,
            "rankings": rankings
        }

        json.dump(cache_data, f, indent=4)
        f.close()

    print("Cache synced successfully.")
    return None

# endregion