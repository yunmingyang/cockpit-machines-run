import os
import sys
import yaml
import json
import socket
import urllib3
import subprocess


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
        if os.environ.get('CI_MESSAGE'):
            if "nightly" in os.environ.get('CI_MESSAGE'):
                print("Don't need to test nightly build")
                sys.exit(1)
                
        http = urllib3.PoolManager()
        compose_id = os.environ.get('COMPOSE_ID') or http.request('GET', 'http://download-node-02.eng.bos.redhat.com/rel-eng/rhel-8/RHEL-8/latest-RHEL-8.1/COMPOSE_ID').data.decode('utf-8').strip()
        compose_status = http.request('GET', 'http://download-node-02.eng.bos.redhat.com/rel-eng/rhel-8/RHEL-8/latest-RHEL-8.1/STATUS').data.decode('utf-8').strip()
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

        with open('{}/run_provision.latest'.format(GlobalVars.workspace_prefix), 'w+') as f:
            subprocess.run('linchpin -vvvv -c {} -w {} up'.format(GlobalVars.linchpin_conf, GlobalVars.linchpin_workspace), 
                           shell=True, 
                           stdout=f)

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

        with open('{}/run_ansible.latest'.format(GlobalVars.workspace_prefix), 'w+') as f:
            subprocess.run('ansible-playbook {}/refresh_podman.yml'.format(GlobalVars.ansible_workspace), 
                           shell=True,
                           stdout=f)


class RunTestSuite():
    @staticmethod
    def execute():
        if subprocess.run('avocado --version', shell=True).returncode:
            print('no avocado, please install')
            sys.exit(1)
        if not os.path.exists(GlobalVars.test_suite + '/test'):
            print('seems that there is no directory of cases, please check.')
            sys.exit(1)
        if not os.path.exists(GlobalVars.environment_file):
            print('need configuration for the test suite')
            sys.exit(1)

        browsers = ['chrome', 'firefox', 'edge']

        with open(GlobalVars.environment_file, 'r') as f:
            test_suite_conf = yaml.load(f, Loader=yaml.FullLoader)

        if not GlobalVars.machines and 'GUEST' not in test_suite_conf.keys():
            print('no machine set, please add -p for the command or set it in the environment_file')
            sys.exit(1)

        os.environ['GUEST'] = GlobalVars.machines or test_suite_conf['GUEST']
        os.environ['HUB'] = test_suite_conf['HUB']
        os.environ['URL_BASE'] = test_suite_conf['URL_BASE']
        os.environ['URLSOURCE'] = test_suite_conf['URLSOURCE']
        os.environ['NFS'] = test_suite_conf['NFS']

        with open('{}/run_avocado.latest'.format(GlobalVars.workspace_prefix), 'w+') as f:
            for browser in browsers:
                os.environ['BROWSER'] = browser
                subprocess.run('avocado run {} -t {} --job-results-dir {}'.format(GlobalVars.test_suite, 'machines', GlobalVars.test_suite_result + '/' + browser),
                               shell=True,
                               stdout=f)


class UploadTestResult():
    @staticmethod
    def execute():
        with open('{}/upload'.format(GlobalVars.workspace_prefix), 'r') as f:
            upload_conf = yaml.load(f, Loader=yaml.FullLoader)

        subprocess.run('scp -r {} root@{}:{}'.format(GlobalVars.test_suite_result,
                                                     upload_conf['RESHOST'],
                                                     upload_conf['RESPATH']),
                       shell=True)
