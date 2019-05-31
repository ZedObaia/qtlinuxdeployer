#!/usr/bin/env python3
import argparse
import atexit
import configparser
import json
import os
import shutil
import signal
import stat
import subprocess
import time

import psutil


def main():
    # Parse arguments and make sure they are valid
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--bin", required=True, help="binary file path")
    ap.add_argument("-o", "--outdir", required=True, help="output directory")
    ap.add_argument("-s", "--srcdir", required=True, help="source directory")

    args = vars(ap.parse_args())
    # get config file
    home = os.path.expanduser("~")
    cfgdir = mkdir(home, '.qtlinuxdeployer')
    cfgfile = os.path.abspath(os.path.join(cfgdir, '.qtlinuxdeployer.cfg'))
    if os.path.isfile(cfgfile):
        config = configparser.ConfigParser()
        config.read(cfgfile)
    else:
        print('Missing config file')

    # extract data from arguments
    outdir = os.path.abspath(args["outdir"])
    binary = os.path.abspath(args["bin"])
    srcdir = os.path.abspath(args["srcdir"])
    if not os.path.isfile(binary):
        ap.exit(ap.print_help())
    atexit.register(exit_handler, os.path.basename(binary))

    dependencies = getDeps(binary)
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
    libdir = mkdir(outdir, 'lib')
    # create plugins dir
    plugindir = mkdir(libdir, 'plugins')

    # start the binary
    pid = forkBinary(binary)
    if pid is not None:
        requiredFiles = getrequiredQtFiles(pid)
        if len(requiredFiles['qml']) > 0:
            # create qml dir if required
            print("Application uses QML")
            if not os.path.exists(os.path.join(libdir, 'qml')):
                os.makedirs(os.path.join(libdir, "qml"))
            qmldir = os.path.join(libdir, 'qml')
        else:
            qmldir = None

        # get plugins and whatnot
        if qmldir:
            extraQml = getQmlFiles(
                config['paths']['binarypath'], srcdir, config['paths']['qmlimportpath'])
            createHierarchy(requiredFiles['qml'], qmldir, '/qml/')
            createHierarchy(extraQml, qmldir, '/qml/')
        createHierarchy(requiredFiles['plugins'], plugindir, '/plugins/')
        createHierarchy(requiredFiles['libs'], libdir, '/lib/')
        # copy binary file
        shutil.copy(binary, outdir)
        # write start script

        writeStartupScript(os.path.abspath(os.path.join(cfgdir, 'template.sh')),
                           outdir, binary)
        # Copy libs to lib dir
        animatedCopy(dependencies, libdir)
        for filename in os.listdir(libdir):
            filepath = os.path.join(libdir, filename)
            if os.path.isfile(filepath) and filename.endswith(config['general']['qtversion']):
                dest = os.path.abspath(filepath).split('so.5', 1)[0] + 'so.5'
                src = os.path.abspath(filepath)
                if not os.path.isfile(dest):
                    os.symlink(src, dest)
    else:
        print('Could not start {}'.format(binary))

# utils section


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def getDeps(filepath):
    procPrepare = subprocess.Popen(
        ["ldd", filepath], stdout=subprocess.PIPE, universal_newlines=True)
    out, err = procPrepare.communicate()
    if err:
        print(err)
    lines = out.split('\n')
    depList = []
    if out:
        for line in lines:
            if "=>" in line:
                depList.append(os.path.abspath(
                    line.split("=>")[1].split('(')[0].strip()))
    return depList


def forkBinary(filepath):
    cleanPreviousServers(os.path.basename(filepath))
    os.system("xvfb-run {} > collector.log 2>&1 &".format(filepath))
    pid = None
    trial = 0
    while pid == None:
        trial += 1
        print('Took #{} trials to create a process'.format(trial), end='\r')
        pid = getProcessByName(os.path.basename(filepath))
    print('')
    return pid


def getProcessByName(pname):
    for proc in psutil.process_iter():
        if proc.name() == pname:
            return proc.pid


def getrequiredQtFiles(procPid):
    procPrepare = subprocess.Popen(["lsof", "-p", str(procPid)],
                                   stdout=subprocess.PIPE, universal_newlines=True)
    out, err = procPrepare.communicate()
    if err:
        print(err)
    QtDeps = []
    allDeps = []
    plugins = []
    qml = []
    libs = []
    lines = out.split('\n')
    for line in lines:
        if "Qt" in line:
            QtDeps.append(line)
    for line in QtDeps:
        for filename in line.split(' '):
            if os.path.isfile(filename):
                allDeps.append(filename.strip())

    for file in allDeps:
        if '/qml/' in file:
            qml.append(file)
        elif '/plugins/' in file:
            plugins.append(file)
        elif '/lib/' in file:
            libs.append(file)
    files = {}
    files['libs'] = libs
    files['plugins'] = plugins
    files['qml'] = qml
    return files


def cleanPreviousServers(filepath=None):
    hitList = []
    hitList.append(getProcessByName("xvfb-run"))
    hitList.append(getProcessByName('Xvfb'))
    hitList.append(getProcessByName(os.path.basename(filepath)))

    for target in hitList:
        if target is not None:
            killProcess(target)


def killProcess(pid):
    os.kill(pid, signal.SIGKILL)


def animatedCopy(filesToCopy, dest):
    FileNames = []
    depCount = len(filesToCopy)
    for filename in filesToCopy:
        FileNames.append(os.path.basename(filename))
    for i, filename in enumerate(filesToCopy):
        if os.path.isdir(filename):
            continue
        shutil.copy(filename, dest)
        time.sleep(0.02)
        suffix = "Copying {} to {}".format(os.path.basename(filename),
                                           os.path.basename(dest)).ljust(len(max(FileNames, key=len))+len(dest))
        printProgressBar(i + 1, depCount, prefix='Copying files:',
                         suffix=suffix, length=50)
    print('Copied files to', dest)


def createHierarchy(filenames, libdirname, delimiter):
    for filename in filenames:
        if '/' in filename.split(delimiter)[1]:
            temp = mkdir(libdirname, filename.split(
                delimiter)[1].rsplit('/', 1)[0])
            shutil.copy(filename, temp)
            if delimiter == '/plugins/' or '.so' in filename and delimiter == '/qml/':
                for i in getDeps(filename):
                    if 'Qt' in os.path.basename(i):
                        shutil.copy(i, os.path.dirname(libdirname))
        else:
            shutil.copy(filename, libdirname)


def mkdir(parent, dirname):
    if not os.path.exists(os.path.join(parent, dirname)):
        os.makedirs(os.path.join(parent, dirname))
    return os.path.join(parent, dirname)


def writeStartupScript(template, dirpath, binary):
    shutil.copy(template, dirpath)
    binaryFileName = os.path.basename(binary)
    newFilePath = os.path.join(dirpath, binaryFileName+'.sh')
    shutil.move(os.path.join(dirpath, os.path.basename(template)),
                newFilePath)
    file = open(newFilePath, 'a')
    file.write('./' + binaryFileName)
    file.close()
    st = os.stat(newFilePath)
    os.chmod(newFilePath, st.st_mode | stat.S_IEXEC)

# using qt's tool qmlimportscanner to get required qml files


def getQmlFiles(binPath, projectDir, qmlimportpath):
    # path for qmlimportscanner binary
    qmlimportscanner = os.path.join(binPath, 'qmlimportscanner')
    if os.path.isfile(qmlimportscanner):
        qmltypes = []
        for file in os.listdir(projectDir):
            if file.endswith(".qml"):
                fileobj = open(os.path.join(projectDir, file))
                for line in fileobj:
                    if 'import' in line:
                        importedModule = line.split(' ')[1]
                        importedModuleVersion = int(
                            float(line.split(' ')[2].strip()))
                        if 'Qt' in importedModule:
                            if importedModule == 'QtQuick' and importedModuleVersion == 2:
                                importedModule = importedModule + \
                                    '.' + str(importedModuleVersion)
                                qmltypes.extend(getAllFiles(
                                    os.path.join(qmlimportpath, importedModule)))
                            else:
                                qmltypes.extend(getAllFiles(os.path.join(
                                    qmlimportpath, importedModule.replace('.', '/'))))

        procPrepare = subprocess.Popen([qmlimportscanner, '-rootPath', projectDir,
                                        '-importPath', qmlimportpath], stdout=subprocess.PIPE, universal_newlines=True)
        out, err = procPrepare.communicate()
        if err:
            print(err)
        data = json.loads(out)
        required = []
        for i in data:
            if 'path' in i and 'plugin' in i:
                required.append(os.path.join(
                    i['path'], "lib{}.so".format(i['plugin'])))
        required.extend(qmltypes)
        return required
    else:
        print('Missing qmlimportscanner')

# clean up at exit


def exit_handler(procName):
    pid = getProcessByName(procName)
    if pid is not None:
        killProcess(pid)
        print('Cleaning up ', procName)
    else:
        print('Nothing to clean up')

# returns a list of files inside a directory recursively


def getAllFiles(dir):
    tempList = []
    for root, dirs, filenames in os.walk(dir):
        for filename in filenames:
            tempList.append(os.path.join(root, filename))
    return tempList


if __name__ == '__main__':
    main()
