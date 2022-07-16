set -x
set -e
rm -rf dixit-api/react_build
cd dixit-web
npm run buildlocal
cd ..
cp -r dixit-web/build/ dixit-api/react_build
(cd dixit-api; pipenv run gunicorn server:app -w=1 -b 0.0.0.0:8000 --threads 8)