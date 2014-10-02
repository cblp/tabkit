# coding: utf-8

from subprocess import Popen, PIPE
from signal import signal, SIGPIPE, SIG_DFL

def safe_popen_args(command):
    return ['/bin/bash', '-o', 'pipefail', '-o', 'errexit', '-c', command]

class SafePopenError(Exception):
    def __init__(self, cmd, status):
        self.cmd = cmd
        self.status = status
        super(SafePopenError, self).__init__(
            'safe_popen failed on %r, status = %r' % (cmd, status)
        )

class SafePopen(Popen):
    def __init__(self, cmdline, bufsize=None, stdin=None, stdout=PIPE):
        popen_args = dict(
            args = safe_popen_args(cmdline),
            shell = False,
            stdin = stdin,
            stdout = stdout,
            preexec_fn = lambda: signal(SIGPIPE, SIG_DFL),
        )
        if bufsize != None:
            popen_args['bufsize'] = bufsize
        super(SafePopen, self).__init__(**popen_args)
        self.__cmdline = cmdline

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.stdin:
            self.stdin.close() # pylint: disable-msg=E1101
        if self.stdout:
            self.stdout.close() # pylint: disable-msg=E1101
        status = self.wait() # pylint: disable-msg=E1101
        if status != 0:
            raise SafePopenError(self.__cmdline, status)

def safe_popen(command, bufsize=None):
    """
    >>> list(safe_popen('echo ok'))
    ['ok\\n']

    >>> list(safe_popen('false; echo ok'))
    Traceback (most recent call last):
        ...
    SafePopenError: safe_popen failed on 'false; echo ok', status = 1

    >>> list(safe_popen('false|true; echo ok'))
    Traceback (most recent call last):
        ...
    SafePopenError: safe_popen failed on 'false|true; echo ok', status = 1
    """
    popen = SafePopen(command, bufsize)
    try:
        for line in popen.stdout: # pylint: disable-msg=E1101
            yield line
    except:
        popen.close()
        raise
    else:
        popen.close()

def safe_system(command, catch_sigpipe=False):
    popen = Popen(
        args = safe_popen_args(command),
        shell = False,
        preexec_fn = lambda: signal(SIGPIPE, SIG_DFL),
    )

    status = popen.wait() # pylint: disable-msg=E1101

    if status == 0:
        return status # все OK

    if catch_sigpipe:
        if status & 128 == 128 and status & 127 == SIGPIPE:
            return status # bash сообщил нам, что его чайлд словил SIGPIPE
        elif status < 0 and -status == SIGPIPE:
            return status # bash лично словил SIGPIPE
            # иногда bash вместо fork/exec делает просто exec (оптимизация, на случай
            # когда нужно выполнить одну простую команду) в таких случаях все выглядит
            # так, как будто сигнал словил баш, хотя на самом деле баша уже давно нет.

    # какая-то ошибка (отличная от SIGPIPE при catch_sigpipe=True)
    raise SafePopenError(command, status)
