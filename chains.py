from steps import *


class Event:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Chains:
    def __init__(self, next=None):
        self.next = next

    def handle(self, event):
        attr = 'handle_{}'.format(event)

        if hasattr(self, attr):
            method = getattr(self, attr)
            method(event)
        elif self.next:
            self.next.handle(event)
        elif hasattr(self, 'handle_default'):
            self.handle_default(event)


class DefaultHandler(Chains):
    def handle_default(self, event):
        raise Exception("unsupport handler: {}".format(event))


class PreprocessingHandler(Chains):
    def handle_preprocessing(self, event):
        print("handle {}: starting...".format(event))
        Preprocessing().execute()
        print("{} finish".format(event))
        print('------------------------------')

class ProvisionHandler(Chains):
    def handle_provision(self, event):
        print("handle {}: starting...".format(event))
        Provision().execute()
        print("{} finish".format(event))
        print('------------------------------')


class ExecAnsibleHandler(Chains):
    def handle_exec_ansible(self, event):
        print("handle {}: starting...".format(event))
        ExecAnsible().execute()
        print("{} finish".format(event))
        print('------------------------------')


class RunTestSuiteHandler(Chains):
    def handle_run_test_suite(self, event):
        print("handle {}: starting...".format(event))
        RunTestSuite().execute()
        print("{} finish".format(event))
        print('------------------------------')