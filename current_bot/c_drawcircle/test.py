import orig_drawcircle
import drawcircle

l1 = list(orig_drawcircle.danger_positions( (0,0), 5))
l2 = drawcircle.danger_positions((0,0), 5)

try:
    assert l1 == l2
    print "TEST OK!!"
    print "l1: ", l1
    print
    print "l2: ", l2
except:
    print "TEST WRONG!!!"
    print "l1: ", l1
    print
    print "l2: ", l2

    print "Elements in l1 missing in l2: ", [x for x in l1 if x not in l2]
    print "Elements in l2 missing in l1: ", [x for x in l2 if x not in l1]

    s1 = set(l1)
    s2 = set(l2)
    print "Equal sets?: ", s1 == s2

l1 = list(orig_drawcircle.can_attack( (0,0), 5))
l2 = drawcircle.can_attack((0,0), 5)

try:
    assert l1 == l2
    print "TEST OK!!"
    print "l1: ", l1
    print
    print "l2: ", l2
except:
    print "TEST WRONG!!!"
    print "l1: ", l1
    print
    print "l2: ", l2

    print "Elements in l1 missing in l2: ", [x for x in l1 if x not in l2]
    print "Elements in l2 missing in l1: ", [x for x in l2 if x not in l1]

    s1 = set(l1)
    s2 = set(l2)
    print "Equal sets?: ", s1 == s2
