# Salto presence project

This will show either a text based list or a web frontend to make a guesstimate who has badged into a Salto operated office.

# Quick-start

```bash
git clone git@github.com:SteveClement/salto-presence.git
cd salto-presence
cp .env.example .env
vi .env
./install_dependencies.sh
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
vi templates/bs.html # Change company name etc for web use
# If you have a custom static/PhotosStaff directory, copy it now
python main.py cli
```

# Short-comings

Currently only ONE reader is considered if a user is present. Ideally the one of the main entrance or the one with the most traffic.

# Authentication against SALTO Space

Ideally you create a new Monitor user under ':8100/index.html#!/operators' with the operator group 'Monitoring and Cardholders'
Issue: If 2FA is enforced, the login will fail, you need to temporarily disable 2FA enforcement to get a bearer token and then you can re-enable 2FA.

# dot env

```
# Make sure to edit .env
cp .env.example .env
```

# Face detection

The face detection is curently used for an OG easter egg.

# MatterMost integration

To get the current status of a user on MatterMost you need to edit: mm.py and add a ~/.netrc file containing an Auth Token (login user/account are not considered but need to be there for not breaking the .netrc file format)

.netrc
```
machine yourMattermostServer.fqdn login foo account foo password theMattermostAuthToken
```

# Dependencies

[HAAR file for face detection](https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml)

OpenCV needs: `apt install libgl-dev`
