Gator - Easily create application-specific custom AMIs
=====================================

Gator creates a custom AMI from just:

* A base AMI ID
* A link to a deb or rpm package that installs your application.

This is useful for many AWS workflows, particularly ones that take advantage of auto-scaling groups.

Requirements
-------------

* Python 3.x
* Linux or UNIX cloud instance (EC2 currently supported)

Installation
-------------
Clone this repository and run:

.. code-block:: bash
    
    # python3 setup.py install

*or*

.. code-block:: bash
    # pip3 install git+https://github.com/Hale-Terminal/gator.git#egg=gator

Usage
-----
::

    usage: gator [-h] [-e ENVIRONMENT] [--version] [--debug] [-n NAME]
                 [-s SUFFIX] [-c CREATOR] (-b BASE_AMI_NAME | -B BASE_AMI_ID)
                 [--ec2-region REGION] [--boto-secure] [--boto-debug]
                 package

    positional arguments:
      package               package to gatorize. A string resolvable by the native
                            package manager or a file system path or http url to
                            the package file.

    optional arguments:
      -h, --help            show this help message and exit
      -e ENVIRONMENT, --environment ENVIRONMENT
                            The environment configuration for gator 
      --version             Show program's version number and exit 
      --debug               Verbose debugging output

    AMI Tagging and Naming:
      Tagging and naming options for the resultant AMI

      -n NAME, --name NAME  name of resultant AMI (default package_name-version-
                            release-arch-yyyymmddHHMM-ebs
      -s SUFFIX, --suffix SUFFIX 
                            suffix of AMI name, (default yyyymmddHHMM)
      -c CREATOR, --creator CREATOR
                            The user who is running gator. The resultant AMI will
                            receive a creator tag w/ this user 

    Base AMI:
      EITHER AMI ID OR NAME, NOT BOTH!

      -b BASE_AMI_NAME, --base-ami-name BASE_AMI_NAME
                            The name of the base AMI used in provisioning
      -B BASE_AMI_ID, --base-ami-id BASE_AMI_ID
                            The id of the base AMI used in provisioning 

    EC2 Options:
      EC2 Connection Information

      --ec2-region REGION   EC2 region (default: us-east-1)
      --boto-secure         connect via https 
      --boto-debug          Boto debug output 

Details
-------
The rough Gator workflow:

#. Create a volume from the snapshot of the base AMI 
#. Attach and mount the volume 
#. Chroot into mounted volume 
#. Provision application onto mounted volume using rpm or deb package
#. Unmount the volume and create a snapshot 
#. Register the snapshot as an AMI