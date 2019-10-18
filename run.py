import os
import sys
import yaml
import secrets
import argparse
from chains import *
from steps import GlobalVars


def init(path):
    GlobalVars.Pinfile_name = 'cockpit-machines'
    GlobalVars.workspace_prefix = path
    GlobalVars.environment_file = '{}/environment_file'.format(GlobalVars.workspace_prefix)
    GlobalVars.linchpin_workspace = '{}/linchpin-workspace'.format(GlobalVars.workspace_prefix)
    GlobalVars.linchpin_conf = '{}/linchpin-workspace/linchpin.conf'.format(GlobalVars.workspace_prefix)
    GlobalVars.ansible_workspace = '{}/ansible-workspace'.format(GlobalVars.workspace_prefix)
    GlobalVars.test_suite = '{}/cockpit'.format(os.environ.get('WORKSPACE', '/root'))
    GlobalVars.test_suite_result = GlobalVars.test_suite + '/result_' + secrets.token_hex(5)
    
    print('Pinfile_name: ', GlobalVars.Pinfile_name)
    print('workspace_prefix: ', GlobalVars.workspace_prefix)
    print('environment_file: ', GlobalVars.environment_file)
    print('linchpin_workspace: ', GlobalVars.linchpin_workspace)
    print('linchpin_conf: ', GlobalVars.linchpin_conf)
    print('ansible_workspace: ', GlobalVars.ansible_workspace)
    print('test_suite: ', GlobalVars.test_suite)
    print('test_suite_result: ', GlobalVars.test_suite_result)

def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('workspace',
                       help='workspace location')
    parse.add_argument('-pre', 
                       '--preprocessing', 
                       dest='preprocessing', 
                       action='store_true', 
                       help='preprocessing step')
    parse.add_argument('-p', 
                       '--provision', 
                       dest='provision', 
                       action='store_true', 
                       help='provision step')
    parse.add_argument('-a', 
                       dest='exec_ansible', 
                       action='store_true', 
                       help='ansible steps')
    parse.add_argument('-r', 
                       '--run', 
                       dest='run_test_suite', 
                       action='store_true', 
                       help='test suite step')
    parse.add_argument('-u', 
                       '--upload', 
                       dest='upload_test_result', 
                       action='store_true', 
                       help='upload test result')

    args = parse.parse_args()
    
    init(args.workspace)

    event_list = []
    handle = DefaultHandler()

    if args.preprocessing:
        event_list.append(Event('preprocessing')) 
        handle = PreprocessingHandler(handle) 
    if args.provision:
        event_list.append(Event('provision'))
        handle = ProvisionHandler(handle)
    if args.exec_ansible:
        event_list.append(Event('exec_ansible'))
        handle = ExecAnsibleHandler(handle)
    if args.run_test_suite:
        event_list.append(Event('run_test_suite'))
        handle = RunTestSuiteHandler(handle)
    if args.upload_test_result:
        event_list.append(Event('upload_test_result'))
        handle = UploadTestResultHandler(handle)

    
    for e in event_list:
        print('------------------------------{} starting...---------------------------'.format(e))
        handle.handle(e)
        print('------------------------------{} finished------------------------------'.format(e))

if __name__ == '__main__':
    sys.exit(main())
