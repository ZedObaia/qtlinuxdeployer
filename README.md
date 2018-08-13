# dependency-collector
## Description
> Tool to create a deploy-able version of your Qt Application for Linux
> - Repo is still in development
> - Not ready for QML yet

## installation
### Debian
`sudo apt-get install xvfb`

`sudo pip3 install -r requirements.txt`

`sudo apt-get install lsof`

## Usage
`./qtlinuxdeployer -b /path/to/binary/file -o /path/to/output/dir`
>This will create set up the output directory with all necessary files to run your application on another linux machine
