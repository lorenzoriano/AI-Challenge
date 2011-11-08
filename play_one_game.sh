#!/usr/bin/env sh
<<<<<<< HEAD
tools/playgame.py -O -E --player_seed 42 --end_wait=0.25 --verbose --log_dir game_logs --turns 500 --map_file tools/maps/maze/maze_04p_01.map  "python tools/sample_bots/python/HunterBot.py" "python tools/sample_bots/python/GreedyBot.py" "python tools/sample_bots/python/GreedyBot.py" "python MyBot.py"
=======
export BROWSER=/usr/bin/firefox
tools/playgame.py -E --turntime=10000 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 100 --map_file tools/maps/maze/maze_04p_01.map  "python MyBot.py" "python tools/sample_bots/python/LeftyBot.py" "python tools/sample_bots/python/HunterBot.py" "python tools/sample_bots/python/GreedyBot.py" --fill --verbose
>>>>>>> 6ac68e8bccf3aeaa85de3873c7d39eb20ccb5812
