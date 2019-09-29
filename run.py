import os
import sys
import yaml
import argparse
from chains import *
from steps import GlobalVars


def init(path='job'):
    if not os.path.exists(path):
        print('no job configuration, please set a configuration file with yaml')
    with open(path, 'r') as f:
        init_conf = yaml.load(f, Loader=yaml.FullLoader)
        
    GlobalVars.Pinfile_name = 'cockpit-machines'
    GlobalVars.workspace_prefix = init_conf['workspace']
    GlobalVars.environment_file = '{}/environment_file'.format(GlobalVars.workspace_prefix)
    GlobalVars.linchpin_workspace = '{}/linchpin-workspace'.format(GlobalVars.workspace_prefix)
    GlobalVars.ansible_workspace = '{}/ansible-workspace'.format(GlobalVars.workspace_prefix)
    GlobalVars.test_suite = '{}/cockpit'.format(os.environ.get('WORKSPACE', '/root'))


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument('conf',
                       help='Configuration file',
                       default='job')
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

    args = parse.parse_args()
    
    init(args.conf)

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

    
    for e in event_list:
        handle.handle(e)

if __name__ == '__main__':
    sys.exit(main())
