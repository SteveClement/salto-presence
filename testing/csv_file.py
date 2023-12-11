#!/usr/bin/env python3

# Test script to work on CSV Audit Trails.
# If realTime is True, your AuditFile needs to be recorded withing 24h


import csv
import glob
import os
from datetime import datetime, timedelta

realTime = False

list_of_files = glob.glob('./Audit*.csv')  # * means all if need specific format then *.csv
latest_file = max(list_of_files, key=os.path.getmtime)

inout = []
firstSeen = set()

with open(latest_file, newline='') as csvfile:
  if realTime:
    nowT = datetime.now()
  else:
    nowT = datetime(2023, 1, 9, 11, 25, 19, 207810)
  #testT = '2023-01-09 11:22:07.909777'
  ins = csv.reader(csvfile, delimiter=',')
  for row in ins:
    curDate = datetime.fromisoformat(row[0])
    if nowT.strftime('%Y-%m-%d') == datetime.fromisoformat(row[0]).strftime('%Y-%m-%d'):
      nextEntry = {"user": row[4], "date": curDate, "count": 1}
      inout.append(nextEntry)
    firstSeen.add(row[4])
    firstSeen.add(str(curDate))

# Make unique
inout_tmp = list({v['user']: v for v in inout}.values())
inout_sorted = sorted(inout_tmp, key=lambda d: d['date'], reverse=True)

for u in inout_sorted:
  hoursAgo = str(timedelta(seconds=(nowT-u["date"]).seconds))[:-3]
  if u['user'] == 'Mx Clement Steve':
    print(f'**** Steve \t last badged {u["date"].strftime("%H:%M")} ({hoursAgo})*****')
  else:
    print(f'{u["user"]} \t last badged {u["date"].strftime("%H:%M")} ({hoursAgo})')
