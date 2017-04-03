-- Initialization
DROP TABLE election;
DROP TABLE ran_in;
DROP TABLE person;
DROP TABLE prior_poll;

CREATE TABLE election (
    PRIMARY KEY (year),
    year int,
    winner varchar(40) references person(name),
    population int,
    num_voted int,
    total_electoral_votes int
);

CREATE TABLE ran_in (
    year int references election(year),
    name varchar(40) references person(name),
    party varchar(40),
    popular_votes int,
    electoral_votes int
);

CREATE TABLE prior_poll (
    year int references election(year),
    name varchar(40) references person(name),
    month varchar(40),
    percent int
);

CREATE TABLE person (
    PRIMARY KEY (name),
    name varchar(40),
    ranking int
);

-- Presidents that need to be hard coded
-- John Tyler
-- Millard Fillmore
-- Andrew Johnson
-- Chester A. Arthur
-- Gerald Ford
