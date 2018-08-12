import subprocess, signal
import os
import psutil
import shutil
import time
import stat

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()
def getDeps(filepath):
    procPrepare =subprocess.Popen(["ldd", filepath], stdout=subprocess.PIPE, universal_newlines=True)
    out, err = procPrepare.communicate()
    lines = out.split('\n')
    depList = []
    if out:
        for line in lines :
            if "=>" in line :
                depList.append(os.path.abspath(line.split("=>")[1].split('(')[0].strip()))
    return depList
def forkBinary(filepath):
    cleanPreviousServers(os.path.basename(filepath))
    os.system("xvfb-run {} > collector.log 2>&1 &".format(filepath))
    pid = None
    trial = 0
    while pid == None:
        trial+=1
        print('Took #{} trials to create a process'.format(trial), end='\r')
        pid = getProcessByName(os.path.basename(filepath))
    print('')
    return pid
def getProcessByName(pname):
    for proc in psutil.process_iter():
        if proc.name() == pname:
            return proc.pid

def getrequiredQtFiles(procPid):
    procPrepare =subprocess.Popen(["lsof", "-p", str(procPid)],
     stdout=subprocess.PIPE, universal_newlines=True)
    out, err = procPrepare.communicate()
    QtDeps = []; allDeps = []; plugins = []; qml = []; libs = []
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
    # for i in plugins:
    #     print('PLUGIN: ',i)
    # for i in libs:
    #     print('LIB: ',i)
    # for i in qml:
    #     print('QML: ', i)
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
        shutil.copy(filename, dest)
        time.sleep(0.02)
        suffix = "Copying {} to {}".format(os.path.basename(filename),
         os.path.basename(dest)).ljust(len(max(FileNames, key=len))+len(dest))
        printProgressBar(i + 1, depCount, prefix = 'Copying files:', suffix = suffix, length = 50)
    print('Copied files to', dest)

def createHierarchy(filenames, libdirname, delimiter):
    for filename in filenames:
        if '/' in filename.split(delimiter)[1]:
            temp = mkdir(libdirname, filename.split(delimiter)[1].rsplit('/', 1)[0])
            shutil.copy(filename, temp)
        else:
            shutil.copy(filename, libdirname)

def mkdir(parent, dirname):
    if not os.path.exists(os.path.join(parent, dirname)):
        os.makedirs(os.path.join(parent,dirname))
    return os.path.join(parent, dirname)

def writeStartupScript(template, dirpath, binary):
    shutil.copy(template, dirpath)
    binaryFileName = os.path.basename(binary)
    newFilePath = os.path.join(dirpath, binaryFileName)
    shutil.move(os.path.join(dirpath, os.path.basename(template)),
     newFilePath)
    file = open(newFilePath, 'a')
    file.write(binary)
    file.close()
    st = os.stat(newFilePath)
    os.chmod(newFilePath, st.st_mode | stat.S_IEXEC)
