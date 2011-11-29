#!/usr/bin/env sh
export BROWSER=/usr/bin/firefox
rm -f current_bot/bot.txt
#tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 1000   "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose --map_file tools/maps/maze/maze_02p_01.map
tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 1000 "python current_bot/MyBot.py" "python oldbot2/oldbot2.py" --fill --verbose --map_file tools/maps/random_walk/random_walk_02p_02.map
#tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 500   "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose --map_file tools/maps/maze/maze_02p_02.map
#tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 500   "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose --map_file tools/maps/random_walk/random_walk_02p_02.map
#tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 500   "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose --map_file tools/maps/random_walk/random_walk_04p_02.map
#tools/playgame.py -E --turntime=200 -O --player_seed 42 --end_wait=0.25 --log_dir game_logs --turns 1000   "python current_bot/MyBot.py"  "python oldbot1/oldbot1.py"  --fill --verbose --map_file tools/maps/random_walk/random_walk_03p_02.map
