import requests
import re
from bs4 import BeautifulSoup

class Election:
    def __init__(self, year, winner, population, num_voted, total_electoral_votes):
        self.year = year
        self.winner = winner
        self.population = population
        self.num_voted = num_voted
        self.total_electoral_votes = total_electoral_votes

        self.ran_ins = []
        self.prior_polls = set()

class RanIn:
    def __init__(self, name, party, popular_votes, electoral_votes):
        self.name = name
        self.party = party
        self.popular_votes = popular_votes
        self.electoral_votes = electoral_votes

class PriorPoll:
    def __init__(self, month, name, percent):
        self.month = month
        self.name = name
        self.percent = percent

class Person:
    def __init__(self, name, ranking):
        self.name = name
        self.ranking = ranking

elections = {}
persons = {}
# e = Election(2016, 'Trump', 1000, 100, 123)
# elections[2016] = e

def load_pop():
    f = open('populations.txt')
    readNext = False
    for line in f:
        num = int(line.replace(',','').strip())
        if readNext == True:
            elections[year].population = num
            readNext = False
            continue
        if (num <= 2016) and ((num == 1789) or (num % 4 == 0)):
            readNext = True
            year = num

def load_elections():
    format_url = 'http://www.270towin.com/{}_Election'
    for year in [1789] + [y for y in range(1792, 2017, 4)]:
        r = requests.get(format_url.format(year))
        html = r.text
        html = r.text.encode('ascii', 'ignore').decode('ascii')
        soup = BeautifulSoup(html, 'html.parser')
        format_year = '{} Election Results'
        keyword = format_year.format(year)
        tbl = soup.find('table', cellspacing='2').find_all('tr')[1:]
        e = Election(year, None, None, None ,None)
        for row in range(0, len(tbl)):
            arr = []
            for td in tbl[row].contents:
                s = td.string
                if s is None:
                    continue
                s = re.sub(r'[^\x00-\x7f]',r' ',s)
                if not s.isspace():
                    arr.append(s.replace('(I)','').strip())
            e_votes = int(re.sub(r'[^\d]+','0',arr[2].replace(',','')))
            pop_votes = 0
            if year > 1820:
                pop_votes = int(re.sub(r'[^\d]+','0',arr[3].replace(',','')))
            if arr[0] != 'Others':
                e.ran_ins.append(RanIn(arr[0], arr[1], pop_votes, e_votes))
                persons[arr[0]] = Person(arr[0], None)

        # John Quincy Adams won from the House of Representatives
        if year == 1824:
            e.winner = e.ran_ins[1].name
        else:
            e.winner = e.ran_ins[0].name
        tev = 0
        tpv = 0
        for r in e.ran_ins:
            tev += r.electoral_votes
            tpv += r.popular_votes
        e.total_electoral_votes = tev
        e.num_voted = tpv
        elections[year] = e

# finds the closest match for name in true_names
# helps normalize different names
def closest_name(name, true_names):
    split_name = name.split()
    def score(true_name):
        s = 0
        for chunk in split_name:
            s += len(chunk) if chunk in true_name else 0
        return s

    return max(true_names, key=score)

def load_prior_polls():
    r = requests.get('https://en.wikipedia.org/wiki/Historical_polling_for_U.S._Presidential_elections')
    soup = BeautifulSoup(r.text.encode('ascii', 'ignore').decode('ascii'), 'html.parser')

    for table in soup.find_all('table', class_='wikitable'):

        election = elections[int(table.caption.b.string)]
        rows = table.find_all('tr')
        names = [ closest_name(th.text, [r.name for r in election.ran_ins])
                for th in rows[0].find_all('th')[1:] ]

        for row in rows[1:len(rows)-2]:
            tds = row.find_all('td')

            # ignore the rows without month labels
            if len(tds) == len(names) + 1:

                month = re.sub(r'\d+|/.*$|\[.*\]', '', tds[0].text) # only take the first month, strip out stuff
                for (name, td) in zip(names, tds[1:]):
                    percent = td.text and int(td.text.replace('%', ''))
                    election.prior_polls.add(PriorPoll(month, name, percent))

def show_results():
    for yr in [1789] + [y for y in range(1792, 2017, 4)]:
        e = elections[yr]
        print(str(yr) + ': ' + e.winner + ' ' + str(e.population) + ' ' + str(e.num_voted) + ' ' + str(e.total_electoral_votes))

def load_persons():
    f = open('rankings.csv')
    for line in f:
        name, ranking = line.split(',')
        persons[name] = Person(name, int(ranking))
    f.close()
    persons['Barack H. Obama'] = Person('Barack H. Obama', None)

def write_sql():
    f = open('load.sql', 'w')

    # copy everything from pre.sql
    with open('pre.sql') as pre:
        for line in pre:
            f.write(line)

    for year in [1789] + [y for y in range(1792, 2017, 4)]:
        e = elections[year]

        f.write('INSERT INTO election VALUES ({}, "{}", {}, {}, {});\n'
                .format( e.year, e.winner, e.population, e.num_voted,
                    e.total_electoral_votes))

        for r in e.ran_ins:
            f.write('INSERT INTO ran_in VALUES ({}, "{}", "{}", {}, {});\n'
                    .format(year, r.name, r.party, r.popular_votes,
                        r.electoral_votes))

        for p in e.prior_polls:
            f.write('INSERT INTO prior_poll VALUES ({}, "{}", "{}", {});\n'
                    .format( year, p.name, p.month, p.percent or 'NULL'))

    for name in persons:
        f.write('INSERT INTO person VALUES ("{}", {});\n'.format(
            name, persons[name].ranking or 'NULL'))

    f.close()
    print('wrote sql to file')

if __name__ == '__main__':
    load_elections()
    load_pop() # missing population values for 2012, 2016
    show_results()
    load_persons()
    load_prior_polls()
    write_sql()
