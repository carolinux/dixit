
### Installation

Before running the app (locally or otherwise), need to install both backend and frontend dependencies. The instructions are for an Ubuntu machine.


## Frontend

`cd dixit-web`

We need node version 12 and npm, in order to manage dependencies and run/compile the frontend. Install it with:

`sudo apt -y install nodejs`

and

`sudo apt -y install npm`

and then verify the installed version (should 12.x) by running

`node --version`

If you're having trouble getting the exact version, use a version manager for Node such as [N](https://blog.logrocket.com/switching-between-node-versions-during-development/).

Install frontend dependencies:

`npm install`

Run it again everytime a dependency is added or changed in package.json

## Backend

`cd dixit-api`

We need Docker, Python 3.6 and pipenv in order to manage dependencies and run the backend (Python server and Redis).
### Install Docker
```sudo snap install docker```
To be able to run Docker without being superuser:
```commandline
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
reboot
```

### Install Python 3.6

`sudo apt-get install python3.6`

If this fails in your distro, do:

```commandline
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.6
sudo apt install python3.6-distutils
```
### Install pipenv

`sudo pip install pipenv`

Then can run (from `dixit-api` directory):

`pipenv install`

to install the dependencies. Run it again whenever the dependencies change in the Pipfile.

## Run app locally

`bash startlocal.sh` -- starts the game at http://0.0.0.0:8000
`bash startlocal.sh --rebuild-react` -- to rebuild the react frontend

Have fun playing different players from different browsers.


## Run in production

### One offs
- Configure the domain name dixit.lucidcode.ch to point to the IP of the production server

- Install the SSL certificate on the production server by following the instructions here: https://certbot.eff.org/instructions?ws=other&os=ubuntufocal

### Release
From the server run `sudo bash startprod.sh`
