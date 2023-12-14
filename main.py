#!/usr/bin/env python3
import json
import os
import os.path
import sys
import time
from datetime import datetime, timedelta
from operator import itemgetter

try:
    import cv2
except:
    print('OpenCV not available')

import requests
from dotenv import dotenv_values
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from PIL import Image, ImageDraw, ImageFont
from unidecode import unidecode

import mm
from bcolors import bcolors

app = Flask(__name__)
Bootstrap(app)

config = dotenv_values()

debug = config['DEBUG']

if len(config) == 0:
    print("Please populate .env to reflect your setup")
    raise SystemExit

global forceReGen
forceReGen = False

sys.path.append("/tmp/")

mmM = mm.MattermostManager()

try:
    os.mkdir("tmp")
except:
    pass

primaryUser = config["PRIMARY_USER"]
baseUrl = config["BASE_URL"]

inout = []

firstSeen = set()
users = set()


@app.route("/")
def main():
    global nowT
    global data
    nowUnix = int(time.time())
    try:
        dataAge = nowUnix - int(os.stat("/tmp/data.py").st_mtime)
        nowT = checkDate()
    except:
        print("/tmp/data.py missing")
    if checkConnection() and not os.path.isfile("/tmp/data.py") or dataAge > 300:
        bear = json.loads(callBear())
        access_token = bear["access_token"]
        today = fetchToday(access_token).decode("utf-8").replace("'", '"')
        data = json.loads(today)
        saveData(str(data))
        # Print the line below to debug faulty data
        # print(data)
        whoIn(data)
    else:
        data = loadData()
        # Print the line below to debug faulty data
        # print(data)
        whoIn(data)
    if len(sys.argv) == 1:
        users = createUserWeb(data)

        return render_template(
            "bs.html",
            len=len(users),
            users=users,
            debug=debug,
            data=data,
            date=str(nowT).split(".")[0],
        )


def createImageOverlay(user, pic, meme=False):
    if meme:
        picNew = pic.strip(".jpg") + str(f"_ovr_{user.split()[0]}.jpg")
        if not os.path.isfile(picNew) or forceReGen:
            img = Image.open(pic)
            I1 = ImageDraw.Draw(img)
            # myFont = ImageFont.truetype('static/Cyberpunk.ttf', 65)
            myFont = ImageFont.truetype("static/new_zelek.ttf", 25)
            I1.text(
                (80, 66), unidecode(user.split()[-1]), font=myFont, fill=(255, 0, 0)
            )
            img.save(picNew)
            img.close()
    else:
        picNew = pic.strip(".jpg") + str("_ovr.jpg")
        thugName = pic.strip(".jpg") + str("_ovr_thug.jpg")
        if not os.path.isfile(picNew) or forceReGen or not os.path.isfile(thugName):
            ext = userHasExt(user)
            if ext == False:
                print(f"User: {user} has no ext?")
            img = Image.open(pic)
            I1 = ImageDraw.Draw(img)
            myFont = ImageFont.truetype("static/Cyberpunk.ttf", 75)
            myFontSmall = ImageFont.truetype("static/new_zelek.ttf", 55)
            # myFont = ImageFont.truetype('static/new_zelek.ttf', 45)
            I1.text(
                (18, 26),
                unidecode(user.split()[-1]).replace("-", " "),
                font=myFont,
                fill=(255, 255, 255),
            )
            I1.text(
                (18, 400),
                f"{ext[0]}\n{ext[1]}\n{ext[2]}",
                font=myFontSmall,
                fill=(255, 255, 255),
            )
            img.save(picNew)
            img.close()

            thugPic = Image.open(pic)
            shades = Image.open("static/shades.png")
            # (223, 473, 90, 90))
            try:
                # Detect face
                faceXY = faceDetect(pic)
                # ('static/PhotosStaff/Mx Clement Steve/pic_web_debug.jpg', (223, 473, 90, 90))
                thugPic.paste(shades, (faceXY[1][0] - 14, faceXY[1][1] + 50), shades)
            except IndexError as e:
                if len(sys.argv) == 1 or debug:
                    print(f"User: {pic} has no face detected.")

            thugPic.save(thugName)
            thugPic.close()


@app.route("/user/<username>/<mode>")
@app.route("/user/<username>")
def profile(username, mode="normie", pic="None"):
    users = createUserWeb(data)
    for user in users:
        if user["user"] == username:
            team = user["team"]
            shortName = user["shortName"]
            extension = user["extension"]
            mmStatus = user["mmStatus"]
            pic = user["pic"]
    pic = pic.split(".")[0] + str("_thug.jpg")
    picDebug = pic.split(".")[0][:-9] + str("_debug.jpg")
    return render_template(
        "profile.html",
        name=username,
        mode=mode,
        pic=pic,
        picDebug=picDebug,
        team=team,
        extension=extension,
        mmStatus=mmStatus,
        shortName=shortName,
    )


def createUserWeb(ins):
    for row in ins:
        curDate = datetime.fromisoformat(row["EventDateTime"])
        if nowT.strftime("%Y-%m-%d") == datetime.fromisoformat(
            row["EventDateTime"]
        ).strftime("%Y-%m-%d"):
            try:
                ext = userHasExt(row["UserData"]["Name"])
                if type(ext) == bool:
                    ext = ["NaN", "NaN", "NaN"]
                nextEntry = {
                    "user": row["UserData"]["Name"],
                    "pic": userHasPic(row["UserData"]["Name"]),
                    "extension": ext[2],
                    "team": ext[1],
                    "shortName": ext[0],
                    "mmStatus": checkMM(ext[3]),
                }
            except KeyError as e:
                print(f"{str(curDate)}  {row['OperationDescription']}")
                continue
            inout.append(nextEntry)
        # TODO: Fix the 2 lines below on KeyError
        # firstSeen.add(row["UserData"]["Name"])
        # firstSeen.add(str(curDate))

    unique = makeUnique(inout)
    users = unique[0]
    inout_sorted = unique[1]

    if len(users) != 0:
        for u in inout_sorted:
            userHasPic(u["user"])
            if u["user"] == primaryUser:
                print("we have primary user")
    else:
        print("No one is in the building.")
    return inout_sorted


def checkDate():
    weekday = datetime.now().weekday()
    if not debug and not (weekday == 5 or weekday == 6):
        nowT = datetime.now()
    else:
        print(bcolors.WARNING + "DEBUG MODE ON" + bcolors.ENDC)
        nowT = datetime.now() - timedelta(days=7 - weekday)
    return nowT


def checkConnection():
    ## try except TimeoutError
    url = baseUrl + "version.txt"
    try:
        r = requests.get(url, timeout=3)
        return True
    except:
        print(f"Cannot reach {baseUrl}")
        raise SystemExit


def checkMM(mail):
    mail = mail.strip("\n")
    now = int(time.time())
    try:
        userID = mmM.getUserID(mail)
        userStatus = mmM.getUserStatus(userID["id"])
        lastActiveDate = datetime.fromtimestamp(
            int(str(userStatus["last_activity_at"])[:-3])
        )
        lastActiveHours = str(
            timedelta(seconds=now - int(str(userStatus["last_activity_at"])[:-3]))
        )
        return userStatus["status"]
    except:
        print(f"Wrong MM E-Mail address: {mail}")
        return "fail"


def faceDetect(imgpath, nogui=True, cascasdepath="haarcascade_frontalface_default.xml"):
    image = cv2.imread(imgpath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(cascasdepath)

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30)
    )

    for x, y, w, h in faces:
        cv2.rectangle(image, (x, y), (x + h, y + h), (0, 255, 0), 2)
        faces = (x, y, w, h)

    if nogui:
        imgpath = imgpath[:-4] + "_debug.jpg"
        cv2.imwrite(imgpath, image)
        return (imgpath, faces)
    else:
        cv2.imshow("Faces found", image)
        cv2.waitKey(0)


# Check if current access token works and return it
def callBear():
    bear = checkBear()
    if bear:
        return bear
    else:
        url = baseUrl + "oauth/connect/token"

        payload = config["SALTO_PAYLOAD"]
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        r = requests.post(url, data=payload, headers=headers)
        saveBear(r.content)

        return r.content


# Check if access token is valid
def checkBear():
    try:
        with open("bear.json", "r") as f:
            bear = json.loads(json.load(f))
    except FileNotFoundError as e:
        return False
    if "error" in bear:
        return False
    else:
        access_token = bear["access_token"]
    result = json.loads(fetchToday(access_token))
    try:
        if result["Message"] == "Expired credentials":
            print("The bear is bad, fetching new one")
            return False
    except TypeError as e:
        return json.dumps(bear)


# Save access token to file
def saveBear(bearer):
    with open("bear.json", "w") as f:
        json.dump(bearer.decode("utf-8").replace("'", '"'), f)


def saveData(data):
    data = "data = " + data
    with open("/tmp/data.py", "w") as f:
        f.write(data)


def loadData():
    try:
        from data import data

        return data
    except (ModuleNotFoundError, SyntaxError) as e:
        print(e)
        raise SystemExit


def fetchToday(bearer):
    url = baseUrl + "rpc/GetAuditTrailEventListByFilter"
    with open("payload_today.json", "r") as f:
        payload = json.load(f)
    # This will get the AuditTrail for the last 24h, has a maxCount of 201, depending on your install some parameters might need to be adapted. The below can be found and sniffed out by doing a query on: index.html#!/audit-trail/advanced-filter
    # If you add an AdvancedFilter on any cardholder [WHO], the accesspoint you want to monitor [WHERE] and 'Door opened (key)' [WHAT] now you should see something like 'StartGetAuditTrailEventListByFilter' which includes the below.
    # TODO: You could also create a filter and figure out its ID to make this cleaner.
    # TODO: Double check if the below is needed as we already load this from file.
    payload = '{"startingItem":null,"maxCount":201,"filter":{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.FilterEngines.AuditTrailFilterEngineForAdvancedFilter","Who":{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.AdvancedFilter.AdvancedAuditTrailFilterWho","AccessLevels":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName<System.Int32>","AdditionalData":1,"Id":-1,"Name":"Any access level"}],"Users":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName<System.Int32>","AdditionalData":2,"Id":-1,"Name":"Any cardholder"}],"Operators":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName<System.Int32>","AdditionalData":1,"Id":-1,"Name":"Any operator"}]},"Where":{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.AdvancedFilter.AdvancedAuditTrailFilterWhere","Zones":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any zone"}],"NodeDevices":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any nodes"}],"AlarmInputs":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any alarm inputs"}],"Relays":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any relays"}],"Doors":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName<System.Int32>","AdditionalData":1,"Id":97,"Name":"Main Entrance"}]},"What":{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.AdvancedFilter.AdvancedAuditTrailFilterWhat","NodeOperations":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any node operation"}],"AlarmInputOperations":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any alarm input operation"}],"RelayOperations":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName","Id":-1,"Name":"Any relay operation"}],"AccessPointOperations":[{"$type":"Salto.Services.Web.Model.Dto.Generic.IdAndName<System.Boolean>","AdditionalData":false,"Id":17,"Name":"Door opened (key)"}],"OperationsGroups":[]},"When":{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.AdvancedFilter.AdvancedAuditTrailFilterWhen","Periods":[{"$type":"Salto.Services.Web.Model.Dto.AuditTrail.AdvancedFilter.AdvancedAuditTrailFilterWhenPeriod","SpecifiedDatePeriodEnabled":false,"StartDatePeriod":"2023-01-09T00:00:00.1","EndDatePeriod":"2023-01-10T00:00:00.1","DayOfWeek":0,"PeriodType":0,"Period":1,"StartTimeInterval":"0001-01-01T00:00:00.0","EndTimeInterval":"0001-01-01T23:59:59.0"}]},"AnyPartition":true,"Partitions":[]},"isForward":true}'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + bearer}

    r = requests.post(url, data=payload, headers=headers)

    return r.content


def whoIn(ins):
    for row in ins:
        curDate = datetime.fromisoformat(row["EventDateTime"])
        if nowT.strftime("%Y-%m-%d") == datetime.fromisoformat(
            row["EventDateTime"]
        ).strftime("%Y-%m-%d"):
            try:
                nextEntry = {
                    "user": row["UserData"]["Name"],
                    "date": curDate,
                    "count": 1,
                }
            except KeyError as e:
                print(f"{str(curDate)}  {row['OperationDescription']}")
                continue
            inout.append(nextEntry)
        # TODO: Fix
        # firstSeen.add(row["UserData"]["Name"])
        # firstSeen.add(str(curDate))
    # print(inout)

    unique = makeUnique(inout)
    users = unique[0]
    inout_sorted = unique[1]
    # raise SystemExit

    if len(users) != 0:
        userNameLength = str(f"<{longestUserName(users) + 5}")
        spacerLength = longestUserName(users) + 40
        print(f"User {str():<15} Time last badged {str():<8}|Time Elapsed")
        print(spacerLength * "=")
        for u in inout_sorted:
            userHasPic(u["user"])
            try:
                hoursAgo = str(timedelta(seconds=(nowT - u["date"]).seconds))[:-3]
            except KeyError as e:
                continue
            if u["user"] == primaryUser:
                primaryIn = f'{u["user"]:{userNameLength}} last badged {str(u["date"].strftime("%H:%M"))} {str():<3}|({hoursAgo})'
                hoursToGo = u["date"] + timedelta(hours=+9)
            else:
                try:
                    print(
                        f'{u["user"]:{userNameLength}} last badged {u["date"].strftime("%Hh%M")} {str():<3}|({hoursAgo})'
                    )
                except KeyError as e:
                    print(f"Key error: {e}")
        print(spacerLength * "=")
        try:
            if primaryIn:
                print(
                    primaryIn
                    + "\nwith 1h break, I can leave at: "
                    + hoursToGo.strftime("%H:%M")
                )
        except UnboundLocalError as e:
            print(f"{primaryUser} is not in the building.")
    else:
        print("No one is in the building.")


def makeUnique(inout):
    # Make unique
    inout_tmp = list({v["user"]: v for v in inout}.values())
    if len(sys.argv) == 1:
        inout_sorted = sorted(
            inout_tmp, key=lambda d: d["user"].split()[-1], reverse=False
        )
    else:
        inout_sorted = sorted(inout_tmp, key=lambda d: d["date"], reverse=True)
    users = []
    for v in inout_sorted:
        users.append(v["user"])
    # print(users)
    return users, inout_sorted


def whenIn(users, user, mode):
    # return first/last login
    return True


def longestUserName(users):
    longest = 0
    for u in users:
        if len(u) > longest:
            longest = len(u)
    return longest


def userHasExt(user):
    ext = "static/PhotosStaff/" + user + "/ext.txt"
    if os.path.isfile(ext):
        with open(ext, "r") as f:
            extension = f.read()
        extension = extension.split(",")
        return extension
    else:
        return False


def userHasPic(user):
    pic = "static/PhotosStaff/" + user + "/pic_web.jpg"
    if os.path.isfile(pic):
        createImageOverlay(user, pic)
        pic = "PhotosStaff/" + user + "/pic_web_ovr.jpg"
        return pic
    else:
        if debug:
            print(f"User {user} has no pic.")
        createImageOverlay(user, "static/no_meme.jpg", True)
        return f"no_meme_ovr_{user.split()[0]}.jpg"


# Broken, please do not use
def openDoor(bearer, uid='{"uid":"7c837988-4c58-4666-a016-c6e4c1e2b216"}'):
    url = baseUrl + "rpc/GetStatusOfExecuteOnlineAccessPointAction"
    payload = '{"action":0,"accessPointIdList":[97]}'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + bearer}

    r = requests.post(url, data=payload, headers=headers)
    print(r.content)


if __name__ == "__main__":
    # The line below exposes a function to the Jinja template
    ##app.jinja_env.globals.update(userHasPic=userHasPic)
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    if len(sys.argv) == 1:
        app.run(debug=debug, host="0.0.0.0", port=8000)
    else:
        main()
