import os
import sys
import yaml
import json
import socket
import secrets
import requests
import subprocess


class GlobalVars:
    machines = ''
    Pinfile_name = ''
    workspace_prefix = ''
    linchpin_workspace = ''
    ansible_workspace = ''
    environment_file = ''
    test_suite = ''


class Preprocessing:
    @staticmethod
    def execute():
        if os.environ.get('CI_MESSAGE'):
            if "nightly" in os.environ.get('CI_MESSAGE'):
                print("Don't need to test nightly build")
                sys.exit(1)

        compose_id = os.environ.get('COMPOSE_ID') or requests.get('http://download-node-02.eng.bos.redhat.com/rel-eng/rhel-8/RHEL-8/latest-RHEL-8.1/COMPOSE_ID').content.decode('utf-8').strip()
        compose_status = requests.get('http://download-node-02.eng.bos.redhat.com/rel-eng/rhel-8/RHEL-8/{}/STATUS'.format(compose_id)).content.decode('utf-8').strip()
        print('the compose id is {}, and status is {}'.format(compose_id, compose_status))

        if compose_status != 'FINISHED':
            print('The compose status is not FINISHED.Skip.')
            sys.exit(1)

        if compose_id:
            with open(GlobalVars.linchpin_workspace + '/PinFile', 'r+') as f:
                conf = yaml.load(f, Loader=yaml.FullLoader)
                conf[GlobalVars.Pinfile_name]['topology']['resource_groups'][0]['resource_definitions'][0]['recipesets'][0]['distro'] = compose_id
                # move the file point to the head of the file, 
                # then clear the file content
                f.seek(0)
                f.truncate()
                yaml.dump(conf, f)
        # TODO: add handle for brew with CI_MESSAGE


class Provision():
    @staticmethod
    def execute():
        if subprocess.run('linchpin --version', shell=True).returncode:
            print('no linchpin, need to install')
            sys.exit(1)
        if not os.path.exists(GlobalVars.linchpin_workspace):
            print('no linchpin_workspace')
            sys.exit(1)

        subprocess.check_output('linchpin -v -w {} up'.format(GlobalVars.linchpin_workspace), shell=True)

        with open('{}/resources/linchpin.latest'.format(GlobalVars.linchpin_workspace), 'r') as f:
            res = json.load(f)

        system = res[list(res.keys())[0]]['targets'][0][GlobalVars.Pinfile_name]['outputs']['resources'][0]['system']
        GlobalVars.machines = socket.gethostbyname(system)


class ExecAnsible():
    @staticmethod
    def execute():
        if subprocess.run('ansible --version', shell=True).returncode:
            print('no ansible, need to install')
            sys.exit(1)
        if not os.path.exists(GlobalVars.ansible_workspace):
            print('no ansbile_workspace')
            sys.exit(1)

        subprocess.check_output('ansible-playbook {}/refresh_podman.yml'.format(GlobalVars.ansible_workspace), shell=True)


class RunTestSuite():
    @staticmethod
    def execute():
        if not subprocess.check_output('avocado --version', shell=True):
            print('no avocado, need to install')
            sys.exit(1)
        if not os.path.exists(GlobalVars.test_suite + '/test'):
            print('seems that there is no directory of cases, please check.')
            sys.exit(1)
        if not os.path.exists(GlobalVars.environment_file):
            print('need configuration for the test suite')
            sys.exit(1)
            
        # make bots for the dependencies of the selenium cases
        subprocess.run('make -C {} bots'.format(GlobalVars.test_suite), 
                       shell=True)

        browsers = ['chrome', 'firefox', 'edge']

        with open(GlobalVars.environment_file, 'r') as f:
            test_suite_conf = yaml.load(f, Loader=yaml.FullLoader)
            
        if not GlobalVars.machines and 'GUEST' not in test_suite_conf.keys():
            print('no machine, need to add -p for the command or set it in the environment_file')
            sys.exit(1)
            
        os.environ['GUEST'] = GlobalVars.machines or test_suite_conf['GUEST']
        os.environ['HUB'] = test_suite_conf['HUB']
        os.environ['URL_BASE'] = test_suite_conf['URL_BASE']
        os.environ['URLSOURCE'] = test_suite_conf['URLSOURCE']
        os.environ['NFS'] = test_suite_conf['NFS']

        res_path = GlobalVars.workspace_prefix + '/result_' + secrets.token_hex(5)
        print('the result path is {}'.format(res_path))

        for browser in browsers:
            os.environ['BROWSER'] = browser
            subprocess.check_output(
                'avocado run {} -t {} --job-results-dir {}'.format(
                    GlobalVars.test_suite, 
                    'machines', 
                    res_path + '/' + browser), 
                shell=True)
