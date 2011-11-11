g++ -O3 astar.cpp micropather.cpp  -fPIC -shared -Wl,-soname,libastar.so -I//usr/include/python2.7 -o libastar.so 
