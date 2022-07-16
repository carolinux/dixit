
### Installation

Before running the app locally, need to install both backend and frontend dependencies.


## Frontend

`cd dixit-web`

We need node version 12 and npm, in order to dependencies and run/compile the frontend. Install it with:

`sudo apt -y install nodejs`

and

`sudo apt -y install npm`

and then verify the installed version (should 12.x) by running

`node --version`

In order to install the project and download the necessary dependencies, run:

`npm install`

Run it again everytime a dependency is added or changed in package.json

## Backend

`cd dixit-api`

We need Python 3.6 and pipenv in order to manage dependencies and run the backend.

`sudo apt-get install python3.6`
`sudo pip install pipenv`

Then can run

`pipenv install`

to install the dependencies. Run it again whenever the dependencies change in the Pipfile.

## Run app locally

`sh startlocal.sh` -- starts the game at http://0.0.0.0:8000


## Run in production

TBA
