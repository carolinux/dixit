has_param() {
    local term="$1"
    shift
    for arg; do
        if [[ $arg == "$term" ]]; then
            return 0
        fi
    done
    return 1
}

set -x
set -e
if has_param '--rebuild-react' "$@"; then
    echo "Rebuilding frontend"
    rm -rf dixit-api/react_build
    cd dixit-web
    npm run buildlocal
    cd ..
    cp -r dixit-web/build/ dixit-api/react_build
fi
docker stop gamescache && docker rm gamescache || true
cp dixit-api/templates/* dixit-api/react_build/
docker run --name gamescache -p 6379:6379 -d redis redis-server
(cd dixit-api; pipenv run gunicorn patched_for_gevent:app -b 0.0.0.0:8000 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1)
#(cd dixit-api; pipenv run python server.py)