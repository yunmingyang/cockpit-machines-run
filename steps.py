import os
import re
import time
import yaml
import json
import socket
import subprocess
from configparser import ConfigParser


class GlobalVars:
    machines = ''
    Pinfile_name = ''
    workspace_prefix = ''
    linchpin_workspace = ''
    ansible_workspace = ''
    environment_file = ''
    test_suite = ''
    test_suite_result = ''


class Preprocessing:
    @staticmethod
    def execute():
        if subprocess.run('bkr --version', shell=True).returncode:
            raise Exception('no bkr, need to install')

        ci_msg = json.loads(os.environ.get('CI_MESSAGE'))
        compose_id = os.environ.get('COMPOSE_ID') or ci_msg['compose_id']
        GlobalVars.test_suite_result = GlobalVars.test_suite_result.format(compose_id)
        print('the compose id is {}'.format(compose_id))
        print('update the location of result: ', GlobalVars.test_suite_result)

        # check distro in ten hours
        count = 0
        while count <= 60:
            if subprocess.run('bkr distros-list --name={}'.format(compose_id)).returncode:
                if count == 60:
                    raise Exception('no distro-list')
                count += 1
                time.sleep(600)
            else:
                break

        with open(GlobalVars.linchpin_workspace + '/PinFile', 'r+') as f:
            conf = yaml.load(f, Loader=yaml.FullLoader)
            conf[GlobalVars.Pinfile_name]['topology']['resource_groups'][0]['resource_definitions'][0]['recipesets'][0]['distro'] = compose_id
            f.seek(0)
            f.truncate()
            yaml.dump(conf, f)


class Provision():
    @staticmethod
    def execute():
        if subprocess.run('linchpin --version', shell=True).returncode:
            raise Exception('no linchpin, need to install')
        if not os.path.exists(GlobalVars.linchpin_workspace):
            raise Exception('no linchpin_workspace')

        provision_cmd = 'linchpin -vvv -c {} -w {} up'.format(GlobalVars.linchpin_conf, GlobalVars.linchpin_workspace)
        provision_proc = subprocess.Popen(provision_cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          shell=True,
                                          encoding='utf-8')
        output, _ = provision_proc.communicate()
        print('linchpin output is:', output, sep='\n')
        if 'Unsuccessful provision of resource' in output or 'failed=1' in output:
            raise Exception('provision failed')

        match = re.search(r'-+[\s\S]cockpit-machines[\s\S]+\d\s', output).group()
        inventory_path = (GlobalVars.linchpin_workspace +
                          '/inventories/' +
                          'provision-' +
                          re.sub(r'[-\s]', '', match)[-7:-1] +
                          '.inventory')
        print('inventory_path is:', inventory_path)
        inventory = ConfigParser()
        inventory.read(inventory_path)
        if len(inventory['all']) != 1:
            raise Exception('too many machines')
        GlobalVars.machines = socket.gethostbyname(dict(inventory['all']).popitem()[-1])


class ExecAnsible():
    @staticmethod
    def execute():
        if subprocess.run('ansible --version', shell=True).returncode:
            raise Exception('no ansible, need to install')
        if not os.path.exists(GlobalVars.ansible_workspace):
            raise Exception('no ansbile_workspace')

        subprocess.run('ansible-playbook {}/refresh_podman.yml'.format(GlobalVars.ansible_workspace), shell=True)


class RunTestSuite():
    @staticmethod
    def execute():
        if subprocess.run('avocado --version', shell=True).returncode:
            raise Exception('no avocado, please install')
        if not os.path.exists(GlobalVars.test_suite + '/test'):
            raise Exception('seems that there is no directory of cases, please check.')
        if not os.path.exists(GlobalVars.environment_file):
            raise Exception('need configuration for the test suite')

        browsers = ['chrome', 'firefox', 'edge']

        with open(GlobalVars.environment_file, 'r') as f:
            test_suite_conf = yaml.load(f, Loader=yaml.FullLoader)

        if not GlobalVars.machines and 'GUEST' not in test_suite_conf.keys():
            raise Exception('no machine set, please add -p for the command or set it in the environment_file')

        os.environ['GUEST'] = GlobalVars.machines or test_suite_conf['GUEST']
        os.environ['HUB'] = test_suite_conf['HUB']
        os.environ['URL_BASE'] = test_suite_conf['URL_BASE']
        os.environ['URLSOURCE'] = test_suite_conf['URLSOURCE']
        os.environ['NFS'] = test_suite_conf['NFS']

        for browser in browsers:
            os.environ['BROWSER'] = browser
            subprocess.run('avocado run {} -t {} --job-results-dir {}'.format(GlobalVars.test_suite, 'machines', GlobalVars.test_suite_result + '/' + browser),
                            shell=True)


class UploadTestResult():
    @staticmethod
    def execute():
        with open('{}/upload'.format(GlobalVars.workspace_prefix), 'r') as f:
            upload_conf = yaml.load(f, Loader=yaml.FullLoader)

        subprocess.run('scp -r {} root@{}:{}'.format(GlobalVars.test_suite_result,
                                                     upload_conf['RESHOST'],
                                                     upload_conf['RESPATH']),
                       shell=True)
