set -x
set -e
rm -rf dixit-api/react_build
cd dixit-web
npm run build
cd ..
cp -r dixit-web/build/ dixit-api/react_build
chown -R carolinux dixit-api/react_build
docker stop gamescache && docker rm gamescache || true
docker run --name gamescache -p 6379:6379 -d redis redis-server
(cd dixit-api; /home/carolinux/.local/share/virtualenvs/dixit-api-EXdWikZD/bin/gunicorn patched_for_gevent:app -w=1 -b 0.0.0.0:443 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --certfile=/etc/letsencrypt/live/dixit.lucidcode.ch/fullchain.pem --keyfile=/etc/letsencrypt/live/dixit.lucidcode.ch/privkey.pem)
