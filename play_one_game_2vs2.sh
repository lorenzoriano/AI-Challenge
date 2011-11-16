#!/usr/bin/env sh
export BROWSER=/usr/bin/firefox
tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 500 --map_file tools/maps/random_walk/random_walk_02p_02.map  "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose
