cython -a drawcircle.pyx
g++ -O3 -fPIC -shared -I/usr/include/python2.7 drawcircle.c -o drawcircle.so
