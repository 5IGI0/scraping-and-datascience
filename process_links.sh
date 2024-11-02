#!/bin/sh

if [ "$#" -ne 1 ]
then
    echo "usage: $0 domain_list.txt"
    exit
fi

export $(cat .env)

if [ "$DATAHUB_TOKEN" != "" ]
then
    echo 'extracting domains...'
    cut -d'/' -f3 "$1"|cut -d':' -f1|cut -d'?' -f1|cut -d'#' -f1|uniq > ."$1".domains
    echo 'removing duplicates...'
    sort ."$1".domains|uniq > ."$1".domains.sort
    echo 'sending domains to datahub...'
    python3 send_domains.py ."$1".domains.sort
    rm ."$1".domains ."$1".domains.sort
else
    echo 'no datahub api key, skipping domain extraction...'
fi

echo "removing duplicated links..."
sort "$1"|uniq > ."$1".sorted
echo 'adding links to the link database...'
python3 store_links.py ."$1".sorted
echo 'adding to archives'
mkdir -p "$ARCHIVE_FOLDER"/links/
xz -czve9 -T15 ."$1".sorted > "$ARCHIVE_FOLDER"/links/"$(date -u --rfc-3339=seconds)".txt.xz
rm ."$1".sorted