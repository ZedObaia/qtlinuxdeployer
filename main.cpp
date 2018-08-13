#include <QCoreApplication>
#include <QDebug>
#include <QLibraryInfo>
#include <QStandardPaths>
#include <QDir>
int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);
    QLibraryInfo *info;
    QStandardPaths *stdpath;
    QString homePath = stdpath->writableLocation(QStandardPaths::HomeLocation);
    QString configFilePath = QDir::cleanPath(homePath + QDir::separator() + ".qtlinuxdeployer" + QDir::separator() + ".qtlinuxdeployer.cfg");
    QString QtBinarypath = info->location(info->BinariesPath);
    QString QmlImportPath = info->location(info->Qml2ImportsPath);
    QString pluginPath = info->location(info->PluginsPath);
    QString QtLibraryPath = info->location(info->LibrariesPath);
    const char *qt_version = qVersion();
    QString version;
    version.sprintf("%s", qt_version);
    QFile file( configFilePath );
    if (file.open(QIODevice::ReadWrite))
    {
        QTextStream stream( &file );
        stream << "[paths]" << endl;
        stream << "libpath="+ QtLibraryPath << endl;
        stream << "binarypath="+ QtBinarypath << endl;
        stream << "qmlimportpath="+ QmlImportPath << endl;
        stream << "pluginpath="+ pluginPath << endl;
        stream << "[general]" << endl;
        stream << "qtversion=" + version << endl;
        qDebug() << "Configuration Finished - Qt version " << version << endl;
        file.close();
    }
    else
    {
        qDebug() << "Could not open " << configFilePath << " for writing" << endl;
    }
    a.exit(1);
}
