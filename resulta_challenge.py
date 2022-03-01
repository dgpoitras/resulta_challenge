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

# list of output fields needed for challenge
score_fields = ['event_id', 'event_date', 'event_time', 'away_team_id', 'away_nick_name', 'away_city', 'home_team_id', 'home_nick_name', 'home_city']

# combining the two for later processing, could have simply created a dictionary, but this seemed more interesting.
zip_iter = zip(score_fields, score_source)
field_dict = dict(zip_iter)

# creating a named tuple as an example as well as ease of access to team data.
Team = namedtuple('Team', 'team_id team rank last_week points modifier adjusted_points')

def parse_arguments():
	"""
	-d is for setting the date, defaulting to today
	-l is for setting the league, deafault NFL
	"""
	parser = argparse.ArgumentParser(description='Get the end date via --commmands')
	parser.add_argument('-d', metavar='date', type=str, default=datetime.now().strftime("%Y-%m-%d"),
		help='set the end date if not today, includes the previous 7 days, default is today, format must be YYYY-MM-DD')
	parser.add_argument('-l', metavar='league', type=str, default='NFL',
		help='set the league for search, default is NFL')
	args = parser.parse_args()
	return args

def get_scoreboard(date_req, league):
	"""
	Retrieves JSON data from destination URL
	Input: date_req(string), league (string)
	output: resp(dict)
	"""
	log.info('initializing')
	# getting a 7 day span from today's date
	start_date = (date_req - timedelta(days=7)).strftime("%Y-%m-%d")
	end_date = date_req.strftime("%Y-%m-%d")

	score_url = f'https://delivery.chalk247.com/scoreboard/{league}/{start_date}/{end_date}.json?{api_key}'

	log.info('getting data from scorboard')
	resp = get(score_url)
	if resp.status_code == 200:
		return resp.json()
	else:
		#very simple error checking, thorough would be to have the more common HTTP responses
		log.error(f'There was an error with the request/response form scorboard URL')
		sys.exit(f'HTTP status code: {resp.status_code}, exiting..')

def get_team_rankings(league):
	"""
	Retrieves JSON data from destination URL
	Input: league (string)
	output: resp (dict)
	"""	
	team_rank_url = f'https://delivery.chalk247.com/team_rankings/{league}.json?{api_key}'
	log.info('getting data for team rankings')
	resp = get(team_rank_url)
	if resp.status_code == 200:
		return resp.json()
	else:
		log.error(f'There was an error with the request/response from team raninkings URL {resp.status_code}')
		sys.exit(f'HTTP status code: {resp.status_code}.\nexiting..')

def process_team_data(resp):
	"""
	Processing all the team data from dict response into a dictionary of team tuples with team id as the key.
	Input: resp (dict)
	output: teams (dict(team_id: Team(tuple)))
	"""	
	# dictionary for all the teams retreived from team ranking page
	teams = {}
	for team in resp['results']['data']:
		# Named tuple for each team, using the team id for easy retrieval when processing
		teams[team['team_id']] = Team(	team_id=team['team_id'], 
									team=team['team'], 
									rank=team['rank'], 
									last_week=team['last_week'], 
									points=team['points'], 
									modifier=team['modifier'], 
									adjusted_points=team['adjusted_points'])
	return teams

def process_output(score_resp, teams):
	"""
	Processsing the final output by merging the desired scoreboard data with the relavent team data.
	Input: score_resp (dict), teams (dict)
	output: output(dict)
	"""
	# initializing list for final ouput
	output = []
	for date, data in score_resp['results'].items():
		# checking if date has any data, omitting if not.
		if data:
			for event_id, values in data['data'].items():
				# Using comprehension to put all the scoreboard values into output dictionary
				single_dict = {k:values[v] for (k, v) in field_dict.items()}
				
				# fixing date and time to separate from single field in source
				single_dict['event_date'] = single_dict['event_date'].split(' ')[0]
				single_dict['event_time'] = single_dict['event_time'].split(' ')[1]

				# adding the pertinent team data from the named tuple dictionary 
				single_dict['away_rank'] = teams[single_dict['away_team_id']].rank
				single_dict['away_rank_points'] = teams[single_dict['away_team_id']].adjusted_points
				single_dict['home_rank'] = teams[single_dict['home_team_id']].rank
				single_dict['home_rank_points'] = teams[single_dict['home_team_id']].adjusted_points

				output.append(single_dict)
	return output



def main(date_str, league):
	"""
	Main method that calls the various working meathods
	input: date_str(string), league(str)
	output: None
	"""
	# testing that the provided date was well formed
	try:
		date_req = datetime.strptime(date_str, '%Y-%m-%d')
	except:
		sys.exit(f'the date format was incorrect, please use YYYY-MM-DD.\nexiting...')

	score_resp = get_scoreboard(date_req, league)
	team_resp = get_team_rankings(league)
	teams = process_team_data(team_resp)
	output = process_output(score_resp, teams)
	log.info(output)
	# could send out the output dict as json in a HTTP reponse, Save to a file as pickeld dict object, as JSON file, or even CSV.


if __name__ == '__main__':
	args = parse_arguments()
	main(args.d, args.l)
