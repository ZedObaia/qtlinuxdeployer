#!/usr/bin/env python3
import argparse
import os
import shutil
import utils
def main():
    # Parse arguments and make sure they are valid
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--bin", required = True, help="binary file path")
    ap.add_argument("-o", "--outdir", required = True, help="output directory")
    args = vars(ap.parse_args())
    # extract data from arguments
    outdir = os.path.abspath(args["outdir"])
    binary = os.path.abspath(args["bin"])
    if not os.path.isfile(binary):
        ap.exit(ap.print_help())
    dependencies = utils.getDeps(binary)
    depFileNames = []
    for filename in dependencies:
        depFileNames.append(os.path.basename(filename))
    # make sure the binary has dependencies
    if not dependencies:
        ap.exit("Please pass dynamically linked Qt binary file")
    # set up output dirs
    # create parent output dir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    # create parent lib dir
    libdir = utils.mkdir(outdir, 'lib')
    # create plugins dir
    plugindir = utils.mkdir(libdir, 'plugins')

    # start the binary
    pid = utils.forkBinary(binary)
    if pid is not None:
        requiredFiles = utils.getrequiredQtFiles(pid)
        if len(requiredFiles['qml']) > 0:
            # create qml dir if required
            if not os.path.exists(os.path.join(libdir, 'qml')):
                os.makedirs(os.path.join(libdir,"qml"))
            qmldir = os.path.join(libdir, 'qml')
        else:
            qmldir = None

        # get plugins and whatnot
        if qmldir:
            utils.createHierarchy(requiredFiles['qml'], qmldir, '/qml/')

        utils.createHierarchy(requiredFiles['plugins'], plugindir, '/plugins/')
        utils.createHierarchy(requiredFiles['libs'], libdir, '/lib/')
        # copy binary file
        shutil.copy(binary, outdir)
        # write start script
        utils.writeStartupScript(os.path.abspath('./template.sh'),
        outdir, binary)
        # Copy libs to lib dir
        utils.animatedCopy(dependencies, libdir)

    else :
        print('Could not start {}'.format(binary))
if __name__ == '__main__':
    main()
