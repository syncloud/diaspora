from subprocess import check_output


DOCKER_SSH_PORT = 2222
SSH = 'ssh -o StrictHostKeyChecking=no -p {0} root@localhost'.format(DOCKER_SSH_PORT)
SCP = 'scp -o StrictHostKeyChecking=no -P {0}'.format(DOCKER_SSH_PORT)


def run_scp(command, throw=True, debug=True, password='syncloud'):
    return _run_command('{0} {1}'.format(SCP, command), throw, debug, password)


def run_ssh(command, throw=True, debug=True, password='syncloud'):
    return _run_command('{0} {1}'.format(SSH, command), throw, debug, password)


def ssh_command(password, command):
    return 'sshpass -p {0} {1}'.format(password, command)


def _run_command(command, throw, debug, password):
    try:
        output = check_output(ssh_command(password, command), shell=True).strip()
        if debug:
            print('ssh command: {0}'.format(command))
            print output
            print
        return output
    except Exception, e:
        print(e.output)
        print(e.message)
        if throw:
            raise e
