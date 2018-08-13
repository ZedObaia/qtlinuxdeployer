#!/usr/bin/env python3
import os
import argparse
import shutil

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qmake", required = True, help="path to desired qmake")
    args = vars(ap.parse_args())
    qmake = args['qmake']
    if not os.path.isfile(qmake):
        ap.print_help()
        ap.exit("Please use valid qmake path")
    home = os.path.expanduser("~")
    cfgdir = mkdir(home, '.qtlinuxdeployer')

    srcdir = os.path.abspath('.')
    files= os.listdir(srcdir)
    for filename in files:
        fullFilename = os.path.join(srcdir, filename)
        if (os.path.isfile(fullFilename)):
            shutil.copy(fullFilename, cfgdir)
    os.chdir(cfgdir)
    os.system(qmake)
    os.system('make')
    os.system('./qtlinuxdeployerconfigtool')
    shutil.copy('./qtlinuxdeployer.py', '/usr/bin')
    shutil.move('/usr/bin/qtlinuxdeployer.py', '/usr/bin/qtlinuxdeployer')
def mkdir(parent, dirname):
    if not os.path.exists(os.path.join(parent, dirname)):
        os.makedirs(os.path.join(parent,dirname))
    return os.path.join(parent, dirname)
if __name__ == '__main__':
    main()
