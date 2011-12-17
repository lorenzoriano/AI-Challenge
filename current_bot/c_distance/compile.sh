cython -a distance.pyx
g++ -O3 -fPIC -shared -I/usr/include/python2.7 distance.c -o distance.so
