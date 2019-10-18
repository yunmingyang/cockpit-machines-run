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
            method()
        elif self.next:
            self.next.handle(event)
        elif hasattr(self, 'handle_default'):
            self.handle_default(event)


class DefaultHandler(Chains):
    def handle_default(self, event):
        raise Exception("unsupport handler: {}".format(event))


class PreprocessingHandler(Chains):
    def handle_preprocessing(self):
        Preprocessing().execute()

class ProvisionHandler(Chains):
    def handle_provision(self):
        Provision().execute()


class ExecAnsibleHandler(Chains):
    def handle_exec_ansible(self):
        ExecAnsible().execute()


class RunTestSuiteHandler(Chains):
    def handle_run_test_suite(self):
        RunTestSuite().execute()


class UploadTestResultHandler(Chains):
    def handle_upload_test_result(self):
        UploadTestResult().execute()