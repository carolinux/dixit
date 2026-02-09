#!/bin/bash
set -x
set -e

# Ensure Redis is running
docker start gamescache 2>/dev/null || docker run --name gamescache -p 6379:6379 -d redis redis-server

(cd dixit-api; pipenv run python -m discord_bot.bot)
