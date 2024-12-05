import MySQLdb
import os
from urllib.parse import urlparse
import idna
from hashlib import sha1
import argparse

from url_sanitize import sanitize_url, is_blacklisted

parser = argparse.ArgumentParser(description='add links to the link database')
parser.add_argument('link_lists', nargs='+')
parser.add_argument('--keep-indexes', action='store_true')
args = parser.parse_args()

mydb = MySQLdb.connect(
  host=os.getenv("LINK_DB_HOST"),
  user=os.getenv("LINK_DB_USER"),
  password=os.getenv("LINK_DB_PASS"),
  database=os.getenv("LINK_DB_DTBS"),
  port=int(os.getenv("LINK_DB_PORT")))

INDEXES = (
    ("`idx_host`", "`scrp_links`", "(`host`)"),
    ("`idx_filename`", "`scrp_links`", "(`filename`)"),
    ("`idx_ext`", "`scrp_links`", "(`ext`)"))

mycursor = mydb.cursor()
# as urllib's ParseResult
mycursor.execute("""
CREATE TABLE IF NOT EXISTS `scrp_links`(
    `hash_id` CHAR(40) NOT NULL,

    `raw`      TEXT NOT NULL,
    `scheme`   TEXT NOT NULL,
    `netloc`   TEXT NOT NULL,
    `path`     TEXT NOT NULL,
    `params`   TEXT NOT NULL,
    `query`    TEXT NOT NULL,
    `fragment` TEXT NOT NULL,
    `username` TEXT,
    `password` TEXT,
    `port`     SMALLINT UNSIGNED,

    -- sanitized values / generated values for indexes
    `host`     VARCHAR(255),
    `filename` VARCHAR(127) GENERATED ALWAYS AS (LEFT(SUBSTRING_INDEX(path, '/', -1),127)) VIRTUAL,
    `ext`      VARCHAR(32)  GENERATED ALWAYS AS (REVERSE(RIGHT(SUBSTRING_INDEX(path, '/', -1),32))) VIRTUAL,

    UNIQUE (`hash_id`)
)""")

if not args.keep_indexes:
    print("dropping indexes...")
    for index in INDEXES:
        print(index[0])
        mycursor.execute("DROP INDEX IF EXISTS "+index[0]+" ON "+index[1])
    mycursor.execute("COMMIT") # idk if it is needed when dropping indexes
    print("done")

INSERT_QUERY = """INSERT IGNORE INTO `scrp_links`(`hash_id`,`raw`,`scheme`,`netloc`,`path`,`params`,`query`,`fragment`,`username`,`password`,`port`,`host`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

rows = []
count = 0

for f in args.link_lists:
    with open(f) as fp:
        for line in fp:
            line = line.strip()
            if line == "":
                continue

            count += 1

            # print(line)
            url = sanitize_url(urlparse(line))
            if is_blacklisted(url):
                continue
            hash_id = sha1(line.encode("utf-8")).hexdigest()

            host = url.hostname
            port = None

            try:
                port = url.port
            except ValueError: # raised if port port<0 or port > 0xFFFF
                pass

            if host:
                try:
                    host = idna.decode(host)
                except:
                    pass
            
            rows.append((hash_id,line,url.scheme,url.netloc,url.path,url.params,url.query,url.fragment,url.username,url.password,port,host))

            if len(rows) >= 10000:
                print("insert", count)
                mycursor.executemany(INSERT_QUERY, rows)
                mycursor.execute("COMMIT")
                rows = []

    mycursor.executemany(INSERT_QUERY, rows)
    mycursor.execute("COMMIT")

    print("creating indexes...")
    for index in INDEXES:
        print(index[0])
        mycursor.execute("CREATE INDEX IF NOT EXISTS "+index[0]+" ON "+index[1]+index[2])
    mycursor.execute("COMMIT") # idk if it is needed when dropping indexes
    print("done")