from flask import Flask, request
import mysql.connector
import json
import os
from decimal import Decimal

app = Flask(__name__)

conn = mysql.connector.connect(
        user    =os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'])

cursor = conn.cursor()

# convert decimals to floats with JSON serializing
def decimal_default(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError

# genericly run and JSON serialize the result
def run(sql_format, **kwargs):
    cursor.execute(sql_format.format(**kwargs))

    return json.dumps({
        'columns': cursor.column_names,
        'data': list(cursor)
    }, default=decimal_default)

@app.route('/election')
def election():
    return run(
        '''
        SELECT e.year, e.winner, e.population, e.num_voted, e.total_electoral_votes,                  r.name, r.party, r.popular_votes, r.electoral_votes, (r.popular_votes / e.num_voted) as percent_popular, (r.electoral_votes / e.total_electoral_votes) as percent_electoral,
               p.month AS prior_poll_month, p.percent AS prior_poll_percent
        FROM election e, ran_in r
        LEFT OUTER JOIN prior_poll p
        ON r.year = p.year AND r.name = p.name
        WHERE e.year = {year} AND r.year = {year};
        ''',
        year=request.args.get('year')
    )

@app.route('/president')
def president():
    return run(
        '''
        SELECT p.name, p.ranking, x.year, x.party, x.popular_votes, x.electoral_votes,
               x.winner, x.population, x.num_voted, x.total_electoral_votes
        FROM person p
        LEFT OUTER JOIN
        (SELECT r.year, r.name, r.party, r.popular_votes, r.electoral_votes,
                e.winner, e.population, e.num_voted, e.total_electoral_votes
         FROM ran_in r, election e
         WHERE r.year = e.year) x
        ON p.name = x.name
        WHERE p.name = '{name}';
        ''',
        name=request.args.get('name')
    )

@app.route('/re-elected')
def re_elected():
    return run(
        '''
        SELECT p.name, e1.year AS first_year, e3.year AS second_year
        FROM election e1, election e2, election e3, person p
        WHERE p.name = e1.winner AND p.name != e2.winner AND p.name = e3.winner
	AND e1.year < e2.year AND e2.year < e3.year;
        '''
    )

@app.route('/swing')
def swing():
    return run(
        '''
        SELECT p.name,
               r1.party AS first_party, r1.year AS first_year, r1.electoral_votes AS first_electoral_votes,
               e1.winner AS first_winner,
               r2.party AS second_party, r2.year AS second_year, r2.electoral_votes AS second_electoral_votes,
               e2.winner AS second_winner
        FROM person p, ran_in r1, ran_in r2, election e1, election e2
        WHERE p.name = r1.name AND r1.name = r2.name AND r1.year < r2.year
	AND r1.party != r2.party AND r1.year = e1.year AND r2.year = e2.year
        ORDER BY p.name;
	'''
    )

@app.route('/party')
def party():
    cursor.execute(
        '''
        SELECT r.party, e.year, r.electoral_votes, r.popular_votes, e.total_electoral_votes, e.num_voted
	FROM election e, ran_in r
	WHERE r.party = '{party}' AND r.year = e.year;
	'''.format(party=request.args.get('party'))
    )
    years = list(cursor)
    yearly_columns = cursor.column_names
    cursor.execute(
        '''
        SELECT r.party, win.count / COUNT(*) AS win_rate,
               SUM(r.electoral_votes) / SUM(e.total_electoral_votes) AS percent_electoral
        FROM election e, ran_in r,
             (SELECT COUNT(*) AS count FROM election e, ran_in r
              WHERE e.winner = r.name AND r.party = '{party}' AND e.year = r.year) win
        WHERE r.party = '{party}' AND r.year = e.year;
        '''.format(party=request.args.get('party'))
    )
    stats = list(cursor)
    stats_columns = cursor.column_names
    return json.dumps({
        'yearly_columns': yearly_columns,
        'yearly_data': years,
        'stats_columns': stats_columns,
        'stats_data': stats
    }, default=decimal_default)

@app.route('/closest')
def closest():
    return run(
        '''
        SELECT e.year, r1.name, r1.popular_votes, r2.name, r2.popular_votes, e.winner,
               (r1.popular_votes - r2.popular_votes) AS popular_vote_difference
	FROM election e, ran_in r1, ran_in r2,
             (SELECT year, MAX(popular_votes) AS max FROM ran_in GROUP BY year) first
	WHERE e.year = first.year AND e.year = r1.year AND e.year = r2.year AND r1.popular_votes = first.max
              AND r2.popular_votes IN
              (SELECT MAX(popular_votes) FROM ran_in WHERE year = first.year AND popular_votes <> first.max)
        ORDER BY r1.popular_votes - r2.popular_votes ASC;
        '''
    )

@app.route('/landslide')
def landslide():
    return run(
        '''
        SELECT e.year, r1.name, r1.popular_votes, r2.name, r2.popular_votes, e.winner,
               (r1.popular_votes - r2.popular_votes) AS popular_vote_difference
	FROM election e, ran_in r1, ran_in r2,
             (SELECT year, MAX(popular_votes) AS max FROM ran_in GROUP BY year) first
	WHERE e.year = first.year AND e.year = r1.year AND e.year = r2.year AND r1.popular_votes = first.max
              AND r2.popular_votes IN
              (SELECT MAX(popular_votes) FROM ran_in WHERE year = first.year AND popular_votes <> first.max)
        ORDER BY (r1.popular_votes - r2.popular_votes) DESC;
        '''
    )

@app.route('/most-popular')
def most_popular():
    return run(
        '''
        SELECT r.name, r.year, (r.popular_votes / e.num_voted) as popularity
        FROM election e, ran_in r
        WHERE e.year = r.year AND r.popular_votes <> 0
        ORDER BY (r.popular_votes / e.num_voted) DESC;
        '''
    )

@app.route('/lowest-ranking')
def lowest_ranking():
    return run(
        '''
        SELECT p.name, p.ranking
	FROM person p
        WHERE p.ranking IS NOT NULL
        ORDER BY p.ranking ASC
        '''
    )

if __name__ == '__main__':
    app.run(debug=True)
