# cockpit-machines-run

## python3 packages
* PyYAML >= 5.1.2
* avocado-framework
* avocado-framework-plugin-result-html
* selenium
## python2 packages
* linchpin
* ansible

## environment prepare
* set an configuration file whose name is environment_file, and it record the test suite environment
* set an linchpin workspace in the same directory of environment_file
* set an ansible workspace in the same directory of environment_file

## how to run
        usage: run.py [-h] [-pre] [-p] [-a] [-r] workspace

        positional arguments:
        workspace             workspace location

        optional arguments:
        -h, --help            show this help message and exit
        -pre, --preprocessing
                                preprocessing step
        -p, --provision       provision step
        -a                    ansible steps
        -r, --run             test suite step
