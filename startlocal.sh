set -x
set -e
rm -rf dixit-api/react_build
cd dixit-web
npm run buildlocal
cd ..
cp -r dixit-web/build/ dixit-api/react_build
# /etc/init.d/lighttpd stop
#pipenv run gunicorn server:app -w=1 -b 0.0.0.0:5000 --threads 8
#pipenv run gunicorn server:app -w=1 -b 0.0.0.0:443 --threads 8 --certfile=/etc/letsencrypt/live/dixit.lucidcode.ch/fullchain.pem --keyfile=/etc/letsencrypt/live/dixit.lucidcode.ch/privkey.pem
(cd dixit-api; pipenv run gunicorn server:app -w=1 -b 0.0.0.0:8000 --threads 8) #--certfile=/etc/letsencrypt/live/dixit.lucidcode.ch/fullchain.pem --keyfile=/etc/letsencrypt/live/dixit.lucidcode.ch/privkey.pem)
