#
#
# Copyright 2022 Hale Terminal LLC
#
#

"""
gator.plugins.finalizer.tagging_s3
==================================
s3 tagging image finalizer
"""
import logging
from shutil import rmtree
from os.path import isdir
from os import makedirs, system

from os import environ
from gator.config import conf_action
from gator.exceptions import VolumeException
from gator.plugins.finalizer.tagging_base import TaggingBaseFinalizerPlugin
from gator.util import randword
from gator.util.linux import sanitize_metadata, monitor_command
from gator.util.metrics import cmdsucceeds, cmdfails, timer

__all__ = ('TaggingS3FinalizerPlugin',)
log = logging.getLogger(__name__)


class TaggingS3FinalizerPlugin(TaggingBaseFinalizerPlugin):
    _name = 'tagging_s3'

    def add_plugin_args(self):
        tagging = super(TaggingS3FinalizerPlugin, self).add_plugin_args()

        context = self._config.context
        tagging.add_argument('-n', '--name', dest='name', action=conf_action(context.ami), help='name of resultant AMI (default package_name-version-release-arch-yyyymmddHHMM-s3')

        tagging.add_argument('--cert', dest='cert', action=conf_action(context.ami), help='The path to the PEM encoded RSA public key certificate file for ec2-bundle-volume')
        tagging.add_argument('--privatekey', dest='privatekey', action=conf_action(context.ami), help='The path to the PEM encoded RSA private key file for ec2-bundle-vol')
        tagging.add_argument('--ec2-user', dest='ec2_user', action=conf_action(context.ami), help='ec2 user id for ec2-bundle-vol')
        tagging.add_argument('--tmpdir', dest='tmpdir', action=conf_action(context.ami), help='temp directory used by ec2-bundle-vol')
        tagging.add_argument('--bucket', dest='bucket', action=conf_action(context.ami), help='the S3 bucket to use for ec2-upload-bundle')
        tagging.add_argument('--break-copy-volume', dest='break_copy_volume', action=conf_action(context.ami, action='store_true'), help='break into shell after copying the volume, for debugging')

    def _set_metadata(self):
        super(TaggingS3FinalizerPlugin, self)._set_metadata()
        context = self._config.context
        config = self._config.plugins[self.full_name]
        metadata = context.package.attributes
        ami_name = context.ami.get('name', None)
        if not ami_name:
            ami_name = config.name_format.format(**metadata)

        context.ami.name = sanitize_metadata('{0}-s3'.format(ami_name))

    def tmpdir(self):
        config = self._config.plugins[self.full_name]
        ami = self._config.context.ami
        return "{0}/{1}".format(ami.get("tmpdir", config.get("default_tmpdir", "/tmp")), ami.name)

    # pylint: disable=access-member-before-definition
    def unique_name(self):
        context = self._config.context
        if hasattr(self, "_unique_name"):
            return self._unique_name
        self._unique_name = "{0}-{1}".format(context.ami.name, randword(6))
        return self._unique_name

    def image_location(self):
        return "{0}/{1}".format(self.tmpdir(), self.unique_name())

    @cmdsucceeds("gator.finalizer.tagging_s3.copy_volume.count")
    @cmdfails("gator.finalizer.tagging_s3.copy_volume.error")
    @timer("gator.finalizer.tagging_s3.copy_volume.duration")
    def _copy_volume(self):
        context = self._config.context
        tmpdir = self.tmpdir()
        if not isdir(tmpdir):
            makedirs(tmpdir)
        return monitor_command(["dd", "bs=65536", "if={0}".format(context.volume.dev), "of={0}".format(self.image_location())])

    @cmdsucceeds("gator.finalizer.tagging_s3.bundle_image.count")
    @cmdfails("gator.finalizer.tagging_s3.bundle_image.error")
    @timer("gator.finalizer.tagging_s3.bundle_image.duration")
    def _bundle_image(self):
        context = self._config.context

        config = self._config.plugins[self.full_name]
        block_device_map = config.default_block_device_map
        root_device = config.default_root_device

        bdm = "root={0}".format(root_device)
        for bd in block_device_map:
            bdm += ",{0}={1}".format(bd[1], bd[0])
        bdm += ",ami={0}".format(root_device)

        cmd = ['ec2-bundle-image']
        cmd.extend(['-c', context.ami.get("cert", config.default_cert)])
        cmd.extend(['-k', context.ami.get("privatekey", config.default_privatekey)])
        cmd.extend(['-u', context.ami.get("ec2_user", str(config.default_ec2_user))])
        cmd.extend(['-i', self.image_location()])
        cmd.extend(['-d', self.tmpdir()])
        if context.base_ami.architecture:
            cmd.extend(['-r', context.base_ami.architecture])

        vm_type = context.ami.get("vm_type", "paravirtual")
        if vm_type == "paravirtual":
            if context.base_ami.kernel_id:
                cmd.extend(['--kernel', context.base_ami.kernel_id])
            if context.base_ami.ramdisk_id:
                cmd.extend(['--ramdisk', context.base_ami.ramdisk_id])
            cmd.extend(['-B', bdm])
        return monitor_command(cmd)

    @cmdsucceeds("gator.finalizer.tagging_s3.upload_bundle.count")
    @cmdfails("gator.finalizer.tagging_s3.upload_bundle.error")
    @timer("gator.finalizer.tagging_s3.upload_bundle.duration")
    def _upload_bundle(self):
        context = self._config.context

        provider = self._cloud._connection.provider
        ak = provider.get_access_key()
        sk = provider.get_secret_key()
        tk = provider.get_security_token()

        cmd = ['ec2-upload-bundle']
        cmd.extend(['-b', context.ami.bucket])
        cmd.extend(['-a', ak])
        cmd.extend(['-s', sk])
        if tk:
            cmd.extend(['-t', tk])
        cmd.extend(['-m', "{0}.manifest.xml".format(self.image_location())])
        cmd.extend(['--retry'])
        return monitor_command(cmd)

    def _register_image(self):
        context = self._config.context
        log.info('Registering image')
        if not self._cloud.register_image(manifest="{0}/{1}.manifest.xml".format(context.ami.bucket, self.unique_name())):
            return False
        log.info('Registration success')
        return True

    def finalize(self):
        log.info('Finalizing image')
        context = self._config.context

        self._set_metadata()

        ret = self._copy_volume()
        if not ret.success:
            log.debug('Error copying volume, failure:{0.command} :{0.std_err}'.format(ret.result))
            return False

        if context.ami.get('break_copy_volume', False):
            system("bash")

        ret = self._bundle_image()
        if not ret.success:
            log.debug('Error bundling image, failure:{0.command} :{0.std_err}'.format(ret.result))
            return False

        ret = self._upload_bundle()
        if not ret.success:
            log.debug('Error uploading bundled volume, failure:{0.command} :{0.std_err}'.format(ret.result))
            return False

        if not self._register_image():
            log.critical('Error registering image')
            return False

        if not self._add_tags(['ami']):
            log.critical('Error adding tags')
            return False

        log.info('Image registered and tagged')
        self._log_ami_metadata()
        return True

    def __enter__(self):
        context = self._config.context
        volume_size = context.ami.get('root_volume_size', None)
        if volume_size is None:
            volume_size = self._cloud.plugin_config.get('root_volume_size', None)
        if volume_size is not None:
            volume_size = int(volume_size)
            if volume_size > int(self.plugin_config.max_root_volume_size):
                raise VolumeException(
                    'Requested root volume size {} exceeds 10G maximum for '
                    'S3-backed AMIs'.format(volume_size))

        environ["GATOR_STORE_TYPE"] = "s3"
        if context.ami.get("name", None):
            environ["GATOR_AMI_NAME"] = context.ami.name
        if context.ami.get("cert", None):
            environ["GATOR_CERT"] = context.ami.cert
        if context.ami.get("privatekey", None):
            environ["GATOR_PRIVATEKEY"] = context.ami.privatekey
        if context.ami.get("ec2_user", None):
            environ["GATOR_EC2_USER"] = context.ami.ec2_user
        if context.ami.get("tmpdir", None):
            environ["GATOR_TMPDIR"] = context.ami.tmpdir
        if context.ami.get("bucket", None):
            environ["GATOR_BUCKET"] = context.ami.bucket

        return super(TaggingS3FinalizerPlugin, self).__enter__()

    def __exit__(self, exc_type, exc_value, trace):
        if exc_type:
            log.debug('Exception encountered in tagging s3 finalizer context manager',
                      exc_info=(exc_type, exc_value, trace))
        # delete tmpdir used by ec2-bundle-vol
        try:
            td = self.tmpdir()
            if isdir(td):
                rmtree(td)
        except Exception:
            log.debug('Exception encountered attempting to clean s3 bundle tmpdir',
                      exc_info=True)
        return False
