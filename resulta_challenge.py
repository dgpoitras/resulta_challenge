##############################################
#
# Script built for employment with resuta as coding challenge
#
# Description: Create a dynamic process to return a list of NFL 
# events in JSON format
#
# By: Derek Poitras
# Date: February 26, 2022
#
###############################################

import sys
import argparse
import logging

from collections import namedtuple
from datetime import datetime, timedelta
from requests import get


log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, 
	format='%(asctime)s %(levelname)s: %(message)s')

# separating api key in case it changes later
api_key = 'api_key=74db8efa2a6db279393b433d97c2bc843f8e32b0'

# list of source fields needed for challenge
score_source = ['event_id', 'event_date', 'event_date','away_team_id', 'away_nick_name', 'away_city', 'home_team_id', 'home_nick_name', 'home_city']
team_source = ['away_rank', 'adjusted_points', 'home_team_id', 'home_nick_name', 'home_city', 'rank']

# list of output fields needed for challenge
score_fields = ['event_id', 'event_date', 'event_time', 'away_team_id', 'away_nick_name', 'away_city', 'home_team_id', 'home_nick_name', 'home_city']
team_fields = ['away_rank', 'away_rank_points', 'home_team_id', 'home_rank_points']

Team = namedtuple('Team', 'team_id team rank last_week points modifier adjusted_points')

def parse_arguments():
	"""Read the argument from the command line"""
	parser = argparse.ArgumentParser(description='Get the end date via --commmands')
	parser.add_argument('-d', metavar='end-date', type=str, default=datetime.now().strftime("%Y-%m-%d"),
		help='set the end date if not today, default is today, format must be YYYY-MM-DD')
	parser.add_argument('-l', metavar='league', type=str, default='NFL',
		help='set the league for search, default is NFL')
	args = parser.parse_args()
	return args

def get_scoreboard(date_req, league):
	log.info('initializing')
	# getting a 7 day span from today's date
	start_date = (date_req - timedelta(days=7)).strftime("%Y-%m-%d")
	end_date = date_req.strftime("%Y-%m-%d")

	# full format "https://delivery.chalk247.com/scoreboard/NFL/<YYYY-MM-DD>/<YYYY-MM-DD>.json?api_key=74db8efa2a6db279393b433d97c2bc843f8e32b0"
	score_url = f'https://delivery.chalk247.com/scoreboard/{league}/{start_date}/{end_date}.json?{api_key}'

	log.info('getting data from scorboard')
	resp = get(score_url)
	if resp.status_code == 200:
		return resp.json()
	else:
		log.error(f'There was an error with the request/response form scorboard URL')
		sys.exit(f'HTTP status code: {resp.status_code}, exiting..')

def get_team_rankings(league):
	team_rank_url = f'https://delivery.chalk247.com/team_rankings/{league}.json?{api_key}'
	log.info('getting data for team rankings')
	resp = get(team_rank_url)
	if resp.status_code == 200:
		return resp.json()
	else:
		log.error(f'There was an error with the request/response from team raninkings URL {resp.status_code}')
		sys.exit(f'HTTP status code: {resp.status_code}.\nexiting..')

def process_team_data(resp):
	teams = {}
	for team in resp['results']['data']:
		teams[team.team_id] = Team(	team_id=team.team_id, 
									team=team.team, 
									rank=team.rank, 
									last_week=team.last_week, 
									points=team.points, 
									modifier=team.modifier, 
									adjusted_points=team.adjusted_points)
	return teams

def process_output(score_resp, teams):
	output = {}
	for date, data in score_resp['results'].items():
		log.debug(f'date type: {type(date)}, data type: {type(data)}')
		log.debug(f'date: {date}, data: {data}')
		if data:
			for event_id, values in data['data'].items():
				log.debug(f'Event ID type: {type(event_id)}, values type: {type(values)}')
				log.debug(f'Event ID: {event_id}, values type: {values}')
				zip_iter = zip(score_fields, score_source)
				single_dict = dict(zip_iter)
				single_dict['event_date'] = split(single_dict['event_date'], ' ')[0]
				single_dict['event_time'] = split(single_dict['event_time'], ' ')[1]
				output[event_id] = single_dict
				log.debug(f'Single Dict: {single_dict}')
	return output



def main(date_str, league):
	try:
		date_req = datetime.strptime(date_str, '%Y-%m-%d')
	except:
		sys.exit(f'the date format was incorrect, please use YYYY-MM-DD.\nexiting...')

	score_resp = get_scorboard(date_req, league)
	team_resp = get_team_rankings(league)
	teams = process_teams(team_reap)
	output = process_output(score_resp, teams)
	log.info(output)


if __name__ == '__main__':
	args = parse_arguments()
	main(args.d, args.l)
