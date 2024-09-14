import csv
import sqlite3

# Define table order to meet foreign key constraints
table_order = ["State", "County", "Town", "LocalAdmin"]

db_create_sql = f'''
DROP TABLE IF EXISTS LocalAdmin;
DROP TABLE IF EXISTS Town;
DROP TABLE IF EXISTS County;
DROP TABLE IF EXISTS State;

CREATE TABLE State (
  woeid INTEGER UNSIGNED NOT NULL,
  iso VARCHAR(2) NOT NULL,
  name TEXT NOT NULL,
  PRIMARY KEY(woeid)
);

CREATE TABLE County (
  woeid INTEGER UNSIGNED NOT NULL,
  iso VARCHAR(2) NOT NULL,
  name TEXT NOT NULL,
  parentid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(woeid),
  FOREIGN KEY(parentid)
    REFERENCES States(woeid)
);

CREATE TABLE LocalAdmin (
  woeid INTEGER UNSIGNED NOT NULL,
  iso VARCHAR(2) NOT NULL,
  name TEXT NOT NULL,
  parentid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(woeid),
  FOREIGN KEY(parentid)
    REFERENCES County(woeid)
);

CREATE TABLE Town (
  woeid INTEGER UNSIGNED NOT NULL,
  iso VARCHAR(2) NOT NULL,
  name TEXT NOT NULL,
  parentid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(woeid),
  FOREIGN KEY(parentid)
    REFERENCES County(woeid)
);
'''

yql_db = sqlite3.connect("yqldb.sqlite")
db_cursor = yql_db.executescript(db_create_sql)

tsv_file = open("geoplanet_places_7.10.0.tsv", "r", encoding='utf-8')
tsv_content = csv.reader(tsv_file, delimiter="\t")

print("Generating database, this may take a while...")

insert_queries = {
    "State": "INSERT INTO State (woeid, iso, name) VALUES (?, ?, ?)",
    "County": "INSERT INTO County (woeid, iso, name, parentid) VALUES (?, ?, ?, ?)",
    "Town": "INSERT INTO Town (woeid, iso, name, parentid) VALUES (?, ?, ?, ?)",
    "LocalAdmin": "INSERT INTO LocalAdmin (woeid, iso, name, parentid) VALUES (?, ?, ?, ?)"
}

grouped_data = {table: [] for table in table_order}

def insert_data(table_name, data):
    for item in data:
        if table_name == "State":
            db_cursor.execute(insert_queries[table_name], (item[0], item[1], item[2]))
        else:
            db_cursor.execute(insert_queries[table_name], (item[0], item[1], item[2], item[5]))
    yql_db.commit()

for content in tsv_content:
    table = content[4]
    if table in table_order:
        grouped_data[table].append(content)

# Optmizing database removing duplicate Town names
local_admin_names = {local[2] for local in grouped_data["LocalAdmin"]}
county_names = {county[2] for county in grouped_data["County"]}

optimized_town = [town for town in grouped_data["Town"] if town[2] not in local_admin_names]
optimized_town = [town for town in optimized_town if town[2] not in county_names]
optimized_local = [local for local in grouped_data["LocalAdmin"] if local[2] not in county_names]

grouped_data["Town"] = optimized_town
grouped_data["LocalAdmin"] = optimized_local

for table in table_order:
    insert_data(table, grouped_data[table])