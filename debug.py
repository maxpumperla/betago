import os
import sys

for x in sys.path:
    print x
    if os.path.isdir(x) and 'site-packages' in x:
        print '***'
        print '\n'.join(os.listdir(x))
        print '***'

