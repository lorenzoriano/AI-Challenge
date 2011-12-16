cython -a c_simulator.pyx
g++ -O3 -fPIC -shared -I/usr/include/python2.7 c_simulator.c -o c_simulator.so
