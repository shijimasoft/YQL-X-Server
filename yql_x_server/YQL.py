import sqlite3
import re

class YQL:
    def __init__(self):
        sqlite_disk_file = sqlite3.connect("yqldb.sqlite")
        self.sqlite_mem_file = sqlite3.connect(":memory:")

        # Load disk database into ram
        sqlite_disk_file.backup(self.sqlite_mem_file)
        sqlite_disk_file.close()

        # Only in the memory database
        self.sqlite_mem_file.execute("CREATE TABLE Generated (woeid INTEGER UNSIGNED PRIMARY KEY, name TEXT NOT NULL)")

    def getWoeidsInQuery(self, q, formatted=False, Legacy=False):
        if formatted:
            return [q] if not isinstance(q, list) else q
        woeids = []
        if Legacy:
            # It's an XML document
            for item in q.iter("id"):
                woeids.append(item.text)
            return woeids
        for woeid in re.findall(r'\b\d+\b', q):
            if not woeid in woeids:
                woeids.append(woeid)
        return woeids
    
    def getWoeidFromName(self, name):
        if not name:
            print("Name is empty")
            return "000000"
        print("Getting woeid from name, " + name)
        try:
            result = self.getSimilarName(name)[0]['woeid']
            print("Woeid from name is " + result)
            return result
        except:
            # Generate woeid from name, store the characters in unicode int format for decoding later
            print("Generating woeid from name, " + name)
            woeid = ""
            for letter in name:
                unicode = str(ord(letter))
                woeid += unicode
            generated_woeids = self.sqlite_mem_file.execute("SELECT woeid FROM Generated").fetchall()
            if not (woeid,) in generated_woeids:
                self.sqlite_mem_file.execute("INSERT INTO Generated (woeid, name) VALUES (?, ?)", (woeid, name))
                self.sqlite_mem_file.commit()
            return woeid

    def getNamesForWoeids(self, woeids):
        names = []
        for woeid in woeids:
            name = self.sqlite_mem_file.execute(
                "SELECT name FROM State WHERE woeid = ? UNION SELECT name FROM County WHERE woeid = ? UNION SELECT name FROM LocalAdmin WHERE woeid = ?",
                (woeid, woeid, woeid)).fetchone()
            if name == None:
                name = self.sqlite_mem_file.execute("SELECT name FROM Generated WHERE woeid = ?", (woeid,)).fetchone()
            names.append(name[0])
        return names

    def getNamesForWoeidsInQ(self, q, formatted=False, nameInQuery=False, Legacy=False):
        if Legacy:
            woeids = []
            # It's an XML document
            for item in q.iter("id"):
                if "|" in item.text:
                    woeids.append(item.text.split("|")[1])
                else:
                    woeids.append(item.text)
            return self.getNamesForWoeids(woeids)
        if not nameInQuery:
            woeids = self.getWoeidsInQuery(q, formatted)
            return self.getNamesForWoeids(woeids)
        else:
            return [q[q.find("query='")+7:q.find(", ")]]

    def getSimilarName(self, q):
        resultsList = []
        query_results = self.sqlite_mem_file.execute("SELECT * FROM County")
        for i in query_results.fetchall():
            if i[2].lower().startswith(q.lower()):
                state = self.sqlite_mem_file.execute("SELECT name FROM State WHERE woeid = ?", (i[3],)).fetchone()
                resultsList.append({
                    "name": i[2],
                    "state": state[0],
                    "iso": i[1],
                    "woeid": i[0],
                    "type": "small"
                })
        query_results = self.sqlite_mem_file.execute("SELECT * FROM LocalAdmin")
        for i in query_results.fetchall():
            if i[2].lower().startswith(q.lower()):
                county = self.sqlite_mem_file.execute("SELECT * FROM County WHERE woeid = ?", (i[3],)).fetchone()
                state = self.sqlite_mem_file.execute("SELECT name FROM State WHERE woeid = ?", (county[3],)).fetchone()
                resultsList.append({
                    "name": i[2],
                    "state": state[0],
                    "iso": i[1],
                    "woeid": i[0],
                    "type": "city"
                })
        query_results = self.sqlite_mem_file.execute("SELECT * FROM Town")
        for i in query_results.fetchall():
            if i[2].lower().startswith(q.lower()):
                county = self.sqlite_mem_file.execute("SELECT * FROM County WHERE woeid = ?", (i[3],)).fetchone()
                if county == None:
                    continue
                state = self.sqlite_mem_file.execute("SELECT name FROM State WHERE woeid = ?", (county[3],)).fetchone()
                resultsList.append({
                    "name": i[2],
                    "state": state[0],
                    "iso": i[1],
                    "woeid": i[0],
                    "type": "city"
                })
        query_results = self.sqlite_mem_file.execute("SELECT * FROM State")
        for i in query_results.fetchall():
            if i[2].lower().startswith(q.lower()):
                resultsList.append({
                    "name": i[2],
                    "state": "",
                    "iso": i[1],
                    "woeid": i[0],
                    "type": "state"
                })

        # Check and remove duplicates
        seen = set()
        places = []
        for place in resultsList:
            if place['name']+place['state'] not in seen:
                places.append(place)
                seen.add(place['name']+place['state'])
        return places