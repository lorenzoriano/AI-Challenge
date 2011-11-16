#!/usr/bin/env sh
export BROWSER=/usr/bin/firefox
tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 500 --map_file tools/maps/maze/maze_06p_01.map  "python MyBot.py"  "python oldbot1/oldbot1.py" "python oldbot1/oldbot1.py" "python  oldbot1/oldbot1.py" --fill --verbose
