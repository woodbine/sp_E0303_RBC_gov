# -*- coding: utf-8 -*-
import os
import re
import requests
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse
from requests.exceptions import ChunkedEncodingError

# Set up variables
entity_id = "E0303_RBC_gov"
url = "http://beta.reading.gov.uk/spendingover500"
errors = 0
user_agent = {'User-agent': 'Mozilla/5.0'}

# Set up functions
def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True
def validateURL(url):
   try:
        opener = urllib2.build_opener()
        r = urllib2.Request(url)
        response = urllib2.urlopen(r)
        count = 1
        while response.getcode() == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            opener = urllib2.build_opener()
            r = urllib2.Request(url)
        sourceFilename = r.headers.get('Content-Disposition')
        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = response.getcode() == 200
        validFiletype = ext in ['.csv', '.xls', '.xlsx']
        return validURL, validFiletype
   except :
          raise

def convert_mth_strings ( mth_string ):

    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
#then replace the word with the number

        mth_string = mth_string.replace(k, v)
    return mth_string
# pull down the content from the webpage
headers = {'User-agent': 'Mozilla/5.0'}
html = requests.get(url, headers = headers)

#html = urllib2.urlopen(url)
soup = BeautifulSoup(html.text, 'html.parser')
#print soup
# find all entries with the required class
blocks = soup.find_all('div', attrs = {'class':'faqanswer'})
for block in blocks:
    links = block.find_all('a', href=True)
    for link in links:
        url = 'http://beta.reading.gov.uk/' +link['href']
        csvfile = link.text
        if '.pdf' not in url:
            csvfiles = csvfile.split('500 ')[-1].replace('-', '').strip().split('to')[-1].strip().split('[')[0].strip().split(' ')
            if len(csvfiles) == 1:
                csvfiles.append('2012')
            csvMth = csvfiles[0][:3]
            csvYr = csvfiles[1]
            csvMth = convert_mth_strings(csvMth.upper())
            if '_to_' or '-to-' in url:
                filename = 'Q'+entity_id + "_" + csvYr + "_" + csvMth
            else:
                filename = entity_id + "_" + csvYr + "_" + csvMth
            todays_date = str(datetime.now())
            file_url = url.strip()
            validFilename = validateFilename(filename)
            validURL, validFiletype = validateURL(file_url)
            if not validFilename:
                print filename, "*Error: Invalid filename*"
                print file_url
                errors += 1
                continue
            if not validURL:
                print filename, "*Error: Invalid URL*"
                print file_url
                errors += 1
                continue
            if not validFiletype:
                print filename, "*Error: Invalid filetype*"
                print file_url
                errors += 1
                continue
            scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
            print filename
if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)
