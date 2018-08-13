# dependency-collector
## Description
> Tool to create a deploy-able version of your Qt Application for Linux
> - Repo is still in development
> - Added minimal support to qml

## installation
### Debian
`sudo apt-get install xvfb`

`sudo pip3 install -r requirements.txt`

`sudo apt-get install lsof`

`./setup.py --qmake /path/to/desired/qmake`

## Usage
`qtlinuxdeployer -b /path/to/binary/file -o /path/to/output/dir -s /path/to/source/diw`
>This will set-up the output directory with all necessary files to run your application on another linux machine
