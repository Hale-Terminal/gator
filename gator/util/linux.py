#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.util.linux
================
Linux utility functions
"""
import errno
import io
import logging
import os
import shutil
import stat
import string
import sys

from collections import namedtuple
from contextlib import contextmanager
from copy import copy
from fcntl import fcntl, F_GETFL, F_SETFL, LOCK_EX, LOCK_UN, LOCK_NB
from fcntl import flock as _flock
from glob import glob
from os import O_NONBLOCK, environ, makedirs
from os.path import isdir, dirname
from select import select
from signal import signal, alarm, SIGALRM
from subprocess import Popen, PIPE

from decorator import decorator


log = logging.getLogger(__name__)
MountSpec = namedtuple('MountSpec', 'dev fstype mountpoint options')
CommandResult = namedtuple('CommandResult', 'success result')
Response = namedtuple('Response', ['command', 'std_err', 'std_out', 'status_code'])
# need to scrub anything not in this list from AMI names and other metadata
SAFE_AMI_CHARACTERS = string.ascii_letters + string.digits + '().-/_'


def command(timeout=None, data=None, *cargs, **ckwargs):
    """
    decorator used to define shell commands to be executed via envoy.run
    decorated function should return a list or string representing the command to be executed
    decorated function should return None if a guard fails
    """
    @decorator
    def _run(f, *args, **kwargs):
        _cmd = f(*args, **kwargs)
        assert _cmd is not None, "null command passed to @command decorator"
        return monitor_command(_cmd, timeout)
    return _run


def set_nonblocking(stream):
    fl = fcntl(stream.fileno(), F_GETFL)
    fcntl(stream.fileno(), F_SETFL, fl | O_NONBLOCK)


def monitor_command(cmd, timeout=None):
    cmdStr = cmd
    shell = True
    if isinstance(cmd, list):
        cmdStr = " ".join(cmd)
        shell = False

    assert cmdStr, "empty command passed to monitor_command"

    log.debug('command: {0}'.format(cmdStr))

    # sanitize PATH if we are running in a virtualenv
    env = copy(environ)
    if hasattr(sys, "real_prefix"):
        env["PATH"] = string.replace(env["PATH"], "{0}/bin:".format(sys.prefix), "")

    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, shell=shell, env=env)
    set_nonblocking(proc.stdout)
    set_nonblocking(proc.stderr)

    stdout = io.open(
        proc.stdout.fileno(), encoding='utf-8', errors='replace', closefd=False)
    stderr = io.open(
        proc.stderr.fileno(), encoding='utf-8', errors='replace', closefd=False)

    if timeout:
        alarm(timeout)

        def handle_sigalarm(*_):
            proc.terminate()
        signal(SIGALRM, handle_sigalarm)

    io_streams = [stdout, stderr]

    std_out = u''
    std_err = u''
    with stdout, stderr:
        while io_streams:
            reads, _, _ = select(io_streams, [], [])
            for fd in reads:
                buf = fd.read(4096)
                if buf is None or len(buf) == 0:
                    # got eof
                    io_streams.remove(fd)
                else:
                    if fd == stderr:
                        log.debug(u'STDERR: {0}'.format(buf))
                        std_err = u''.join([std_err, buf])
                    else:
                        if buf[-1] == u'\n':
                            log.debug(buf[:-1])
                        else:
                            log.debug(buf)
                        std_out = u''.join([std_out, buf])

    proc.wait()
    std_out = std_out.encode('utf-8')
    std_err = std_err.encode('utf-8')
    alarm(0)
    status_code = proc.returncode
    log.debug("status code: {0}".format(status_code))
    return CommandResult(status_code == 0, Response(cmdStr, std_err, std_out, status_code))


def mounted(mountspec):
    pat = mountspec.mountpoint.strip() + ' '
    with open('/proc/mounts') as mounts:
        return any(pat in mount for mount in mounts)


def fsck(dev):
    cmd = monitor_command(['fsck', '-y', '-f', dev])
    # e2fsck will exit 1 if it finds and corrects filesystem problems.
    # consider that a success but fail all other exits as they should be legitimate
    # problems that prevent a bake.
    if not cmd.success and cmd.result.status_code == 1:
        cmd = CommandResult(True, cmd.result)
    return cmd


def resize2fs(dev):
    return monitor_command(['resize2fs', dev])


def growpart(dev, part):
    cmd = monitor_command(['growpart', dev, part])
    # growpart exits 1 when there is no free space to grow into, exits 2
    # when a legitimate error is thrown
    if not cmd.success and cmd.result.status_code == 1:
        cmd = CommandResult(True, cmd.result)
    return cmd


def mount(mountspec):
    if not any((mountspec.dev, mountspec.mountpoint)):
        log.error('Must provide dev or mountpoint')
        return None

    fstype_arg = options_arg = None

    mountpoint = mountspec.mountpoint

    if mountspec.fstype:
        if mountspec.fstype == 'bind':
            fstype_flag = '-o'
            # we may need to create the mountpoint if it does not exist
            if not isdir(mountspec.dev):
                mountpoint = dirname(mountspec.mountpoint)
        else:
            fstype_flag = '-t'
        fstype_arg = '{0} {1}'.format(fstype_flag, mountspec.fstype)

    if not isdir(mountpoint):
        makedirs(mountpoint)

    if mountspec.options:
        options_arg = '-o ' + mountspec.options

    cmd = ['mount']
    if fstype_arg is not None:
        cmd.append(fstype_arg)
    if options_arg is not None:
        cmd.append(options_arg)
    cmd.extend([mountspec.dev, mountspec.mountpoint])
    return monitor_command(' '.join(cmd))


def unmount(mountspec, verbose=True, recursive=False):
    cmd = ['umount']
    if verbose:
        cmd.append('--verbose')
    if recursive:
        cmd.append('--recursive')
    cmd.append(mountspec.mountpoint)
    return monitor_command(cmd)


def busy_mount(mountpoint):
    lsof = monitor_command(['lsof', '-X', mountpoint])
    # lsof against a bind-mounted /dev will show open handles against /dev
    # so filter such that we only return open handles explicitly containing
    # the mountpoint
    if not lsof.success or len(lsof.result.std_out) == 0:
        return lsof
    stdout_lines = lsof.result.std_out.split('\n')
    header = stdout_lines[0]
    filtered_lines = [line for line in stdout_lines if mountpoint in line]
    new_success = len(filtered_lines) > 0
    new_out = '\n'.join([header] + filtered_lines)
    # repackage the response
    resp = Response(
        lsof.result.command, lsof.result.std_err, new_out, lsof.result.status_code)
    return CommandResult(new_success, resp)


def sanitize_metadata(word):
    chars = list(word)
    for index, char in enumerate(chars):
        if char not in SAFE_AMI_CHARACTERS:
            chars[index] = '_'
    return ''.join(chars)


def keyval_parse(record_sep='\n', field_sep=':'):
    """decorator for parsing CommandResult stdout into key/value pairs returned in a dict
    """
    @decorator
    def _parse(f, *args, **kwargs):
        return result_to_dict(f(*args, **kwargs), record_sep, field_sep)
    return _parse


def result_to_dict(commandResult, record_sep='\n', field_sep=':'):
    metadata = {}
    if commandResult.success:
        for record in commandResult.result.std_out.split(record_sep):
            try:
                key, val = record.split(field_sep, 1)
            except ValueError:
                continue
            metadata[key.strip()] = val.strip()
    else:
        log.debug('failure:{0.command} :{0.std_err}'.format(commandResult.result))
    return metadata


class Chroot(object):
    def __init__(self, path):
        self.path = path
        log.debug('Chroot path: {0}'.format(self.path))

    def __enter__(self):
        log.debug('Configuring chroot at {0}'.format(self.path))
        self.real_root = os.open('/', os.O_RDONLY)
        self.cwd = os.getcwd()
        os.chroot(self.path)
        os.chdir('/')
        log.debug('Inside chroot')
        return self

    def __exit__(self, typ, exc, trc):
        if typ:
            log.debug('Exception encountered in Chroot', exc_info=(typ, exc, trc))
        log.debug('Leaving chroot')
        os.fchdir(self.real_root)
        os.chroot('.')
        os.chdir(self.cwd)
        log.debug('Outside chroot')
        return False


def lifo_mounts(root):
    """return list of mount points mounted on 'root'
    and below in lifo order from /proc/mounts."""
    with open('/proc/mounts') as proc_mounts:
        # grab the mountpoint for each mount where we MIGHT match
        mount_entries = [line.split(' ')[1] for line in proc_mounts if root in line]
    if not mount_entries:
        # return an empty list if we didn't match
        return mount_entries
    return [entry for entry in reversed(mount_entries) if entry == root or entry.startswith(root + '/')]


def copy_image(src=None, dst=None):
    """dd like utility for copying image files.
       eg.
       copy_image('/dev/sdf1','/mnt/bundles/ami-name.img')
    """
    try:
        src_fd = os.open(src, os.O_RDONLY)
        dst_fd = os.open(dst, os.O_WRONLY | os.O_CREAT, 0o644)
        blks = 0
        blksize = 64 * 1024
        log.debug("copying {0} to {1}".format(src, dst))
        while True:
            buf = os.read(src_fd, blksize)
            if len(buf) <= 0:
                log.debug("{0} {1} blocks written.".format(blks, blksize))
                os.close(src_fd)
                os.close(dst_fd)
                break
            out = os.write(dst_fd, buf)
            if out < blksize:
                log.debug('wrote {0} bytes.'.format(out))
            blks += 1
    except OSError as e:
        log.debug("{0}: errno[{1}]: {2}.".format(e.filename, e.errno, e.strerror))
        return False
    return True


@contextmanager
def flock(filename=None):
    """simple blocking exclusive file locker
       eg:
       with flock(lockfilepath):
           ...
    """
    with open(filename, 'a') as fh:
        _flock(fh, LOCK_EX)
        yield
        _flock(fh, LOCK_UN)


def locked(filename=None):
    """
    :param filename:
    :return: True if file is locked.
    """
    with open(filename, 'a') as fh:
        try:
            _flock(fh, LOCK_EX | LOCK_NB)
            ret = False
        except IOError as e:
            if e.errno == errno.EAGAIN:
                log.debug('{0} is locked: {1}'.format(filename, e))
                ret = True
            else:
                ret = False
    return ret


def root_check():
    """
    Simple root gate
    :return: errno.EACCESS if not running as root, None if running as root
    """
    if os.geteuid() != 0:
        return errno.EACCES
    return None


def is_nvme():
    return any(glob('/sys/block/nvme*n*'))


# on NVMe instances with udev rules configured, /dev/<prefix>* will be symlinks to
# the real NVMe block devices under /sys/block
def nvme_device_prefix(prefixes):
    log.debug('Getting OS-native device prefix from candidates: {}'.format(prefixes))
    log.debug('NVMe system detected, searchinig /dev')
    devpat = '/dev/{}*'
    for prefix in prefixes:
        devices = glob(devpat.format(prefix))
        if any(devices):
            test_device = devices[0]
            if not os.path.islink(test_device):
                log.debug('Device {} does not appear to be a symlink, skipping'.format(test_device))
                continue
            # sanity check
            target = os.path.realpath(test_device)
            if not os.path.exists(target):
                log.debug('Device {} points to {} which does not exist, '
                          'skipping'.format(test_device, target))
                continue
            if not target.startswith('/dev/nvme'):
                log.debug('Device {} points to {} which does not appear to be '
                          'NVMe, skipping'.format(test_device, target))
                continue
            log.debug('Device {} points to {}, prefix is {}'.format(test_device, target, prefix))
            return prefix

    else:
        log.debug('No candidates found under /dev, falling back to standard search')
        return standard_device_prefix(prefixes)


def standard_device_prefix(prefixes):
    log.debug('Getting OS-native device prefix from candidates: {}'.format(prefixes))
    log.debug('Non-NVMe system or NVMe-fallback, searching /sys/block')
    devpat = '/sys/block/{}*'
    for prefix in prefixes:
        if any(glob(devpat.format(prefix))):
            log.debug('Prefix {} derived from existing devices under /sys/block'.format(prefix))
            return prefix
    else:
        log.error('Unable to determine block device prefix from candidates: {}'.format(prefixes))
        return None


def native_device_prefix(prefixes):
    return nvme_device_prefix(prefixes) if is_nvme() else standard_device_prefix(prefixes)


def device_prefix(source_device):
    log.debug('Getting prefix for device {0}'.format(source_device))
    # strip off any incoming /dev/ foo
    source_device_name = os.path.basename(source_device)
    # if we have a subdevice/partition...
    if source_device_name[-1].isdigit():
        # then its prefix is the name minus the last TWO chars
        log.debug('Device prefix for {0} is {1}'.format(source_device, source_device_name[:-2:]))
        return source_device_name[:-2:]
    else:
        # otherwise, just strip the last one
        log.debug('Device prefix for {0} is {1}'.format(source_device, source_device_name[:-1:]))
        return source_device_name[:-1:]


def native_block_device(source_device, native_prefix):
    source_device_prefix = device_prefix(source_device)
    if source_device_prefix == native_prefix:
        # we're okay, using the right name already, just return the same name
        return source_device
    else:
        # sub out the bad prefix for the good
        return source_device.replace(source_device_prefix, native_prefix)


def os_node_exists(dev):
    try:
        mode = os.stat(dev).st_mode
    except OSError:
        return False
    return stat.S_ISBLK(mode)


def install_provision_config(src, dstpath, backup_ext='_aminator'):
    if os.path.isfile(src) or os.path.isdir(src):
        log.debug('Copying {0} from the aminator host to {1}'.format(src, dstpath))
        dst = os.path.join(dstpath.rstrip('/'), src.lstrip('/'))
        log.debug('copying src: {0} dst: {1}'.format(src, dst))
        try:
            if os.path.isfile(dst) or os.path.islink(dst) or os.path.isdir(dst):
                backup = '{0}{1}'.format(dst, backup_ext)
                log.debug('Making backup of {0}'.format(dst))
                try:
                    if os.path.isdir(dst) or os.path.islink(dst):
                        try:
                            os.rename(dst, backup)
                        except OSError as e:
                            if e.errno == 18:  # EXDEV Invalid cross-device link
                                # need to copy across devices
                                if os.path.isdir(dst):
                                    shutil.copytree(dst, backup, symlinks=True)
                                    shutil.rmtree(dst)
                                elif os.path.islink(dst):
                                    link = os.readlink(dst)
                                    os.remove(dst)
                                    os.symlink(link, backup)

                    elif os.path.isfile(dst):
                        shutil.copy(dst, backup)
                except Exception:
                    errstr = 'Error encountered while copying {0} to {1}'.format(dst, backup)
                    log.critical(errstr)
                    log.debug(errstr, exc_info=True)
                    return False
            if os.path.isdir(src):
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy(src, dst)
        except Exception:
            errstr = 'Error encountered while copying {0} to {1}'.format(src, dst)
            log.critical(errstr)
            log.debug(errstr, exc_info=True)
            return False
        log.debug('{0} copied from aminator host to {1}'.format(src, dstpath))
        return True
    else:
        log.critical('File not found: {0}'.format(src))
        return True


def install_provision_configs(files, dstpath, backup_ext='_aminator'):
    for filename in files:
        if not install_provision_config(filename, dstpath, backup_ext):
            return False
    return True


def remove_provision_config(src, dstpath, backup_ext='_aminator'):
    dst = os.path.join(dstpath.rstrip('/'), src.lstrip('/'))
    backup = '{0}{1}'.format(dst, backup_ext)
    try:
        if os.path.isfile(dst) or os.path.islink(dst) or os.path.isdir(dst):
            try:
                if os.path.isdir(dst):
                    log.debug('Removing {0}'.format(dst))
                    shutil.rmtree(dst)
                    log.debug('Provision config {0} removed'.format(dst))
            except Exception:
                errstr = 'Error encountered while removing {0}'.format(dst)
                log.critical(errstr)
                log.debug(errstr, exc_info=True)
                return False

        if os.path.isfile(backup) or os.path.islink(backup) or os.path.isdir(backup):
            log.debug('Restoring {0} to {1}'.format(backup, dst))
            if os.path.isdir(backup) or os.path.islink(backup):
                os.rename(backup, dst)
            elif os.path.isfile(backup):
                shutil.copy(backup, dst)
            log.debug('Restoration of {0} to {1} successful'.format(backup, dst))
        else:
            log.warn('No backup file {0} was found'.format(backup))
    except Exception:
        errstr = 'Error encountered while restoring {0} to {1}'.format(backup, dst)
        log.critical(errstr)
        log.debug(errstr, exc_info=True)
        return False
    return True


def remove_provision_configs(sources, dstpath, backup_ext='_aminator'):
    for filename in sources:
        if not remove_provision_config(filename, dstpath, backup_ext):
            return False
    return True


def short_circuit(root, cmd, ext='short_circuit', dst='/bin/true'):
    fullpath = os.path.join(root.rstrip('/'), cmd.lstrip('/'))
    if os.path.isfile(fullpath):
        try:
            log.debug('Short circuiting {0}'.format(fullpath))
            os.rename(fullpath, '{0}.{1}'.format(fullpath, ext))
            log.debug('{0} renamed to {0}.{1}'.format(fullpath, ext))
            os.symlink(dst, fullpath)
            log.debug('{0} linked to {1}'.format(fullpath, dst))
        except Exception:
            errstr = 'Error encountered while short circuiting {0} to {1}'.format(fullpath, dst)
            log.critical(errstr)
            log.debug(errstr, exc_info=True)
            return False
        else:
            log.debug('short circuited {0} to {1}'.format(fullpath, dst))
            return True
    else:
        log.error('{0} not found'.format(fullpath))
        return False


def short_circuit_files(root, cmds, ext='short_circuit', dst='/bin/true'):
    for cmd in cmds:
        if not short_circuit(root, cmd, ext, dst):
            return False
    return True


def rewire(root, cmd, ext='short_circuit'):
    fullpath = os.path.join(root.rstrip('/'), cmd.lstrip('/'))
    if os.path.isfile('{0}.{1}'.format(fullpath, ext)):
        try:
            log.debug('Rewiring {0}'.format(fullpath))
            os.remove(fullpath)
            os.rename('{0}.{1}'.format(fullpath, ext), fullpath)
            log.debug('{0} rewired'.format(fullpath))
        except Exception:
            errstr = 'Error encountered while rewiring {0}'.format(fullpath)
            log.critical(errstr)
            log.debug(errstr, exc_info=True)
            return False
        else:
            log.debug('rewired {0}'.format(fullpath))
            return True
    else:
        log.error('{0}.{1} not found'.format(fullpath, ext))
        return False


def rewire_files(root, cmds, ext='short_circuit'):
    for cmd in cmds:
        if not rewire(root, cmd, ext):
            return False
    return True


def mkdir_p(path):
    try:
        if os.path.isdir(path):
            return

        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise e
