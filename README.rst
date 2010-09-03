==========================================================
 ``gitosis-ng`` -- software for hosting ``git`` repositories
==========================================================

    Manage ``git`` repositories, provide access to them over SSH,
    manage them over SSH, with tight access control 
    and not needing shell accounts.

``gitosis-ng`` is a fork of the ``gitosis`` project which adds
additional features to help users and admins interact directly with
the ``gitosis-ng`` server by sending simple commands via SSH.

I created this fork because I wanted a simple way for my users (developers)
to be able to list all of the git repositories hosted on the server.
This quickly morphed into wanting to give users other commands, such as
adding repos on their own so they did not have to wait for an
admin to do it.  Then, I realized I could give the same kind of simple
command-based control to the admins.

``gitosis-ng`` is licensed under the GPL, see the file ``COPYING`` for
more information.


What makes ``gitosis-ng`` different from ``gitosis``?
=====================================================

Not a whole lot, actually.  ``gitosis`` is a great piece of software
and all of its functionality still remains.  If you are familiar
with using ``gitosis``, the transition to ``gitosis-ng`` will
be trivial.

``gitosis-ng`` extends the functionality of ``gitosis`` by
adding the following features:

- Allow users and admins to interact with the ``gitosis-ng`` server via SSH commands, eg::

    ssh git@GIT_SERVER help
    ssh git@GIT_SERVER list
    ssh git@GIT_SERVER list-short
    ssh git@GIT_SERVER add-repo my-project

- Allow admins to configure ACLs on a per-repository basis by specifying "readonly = user1" and "writeable = user2 user3" within the "[repo myproject]" section of the ``gitosis.conf`` file.


Upgrading from ``gitosis`` to ``gitosis-ng``
============================================

- Backup your ~git home directory first!

- Download the latest gitosis-ng code::

	git clone git://github.com/joemiller/gitosis-ng.git

- Install gitosis-ng::

	cd gitosis-ng
	python setup.py install

- That's it.


Setting it up from scratch
==========================

These directions are specific to CentOS/RHEL 5.x, but the concepts
simple enough to translate to other platforms.

- Setup DAG and EPEL Yum repos.  We will need some RPMs from the DAG rpmforge
  and EPEL yum repos.  EPEL contains git 1.5, DAG contains git 1.7.  Both
  should work with gitosis-ng, but testing was done with 1.7

::

    DAG rpmforge:
	rpm -Uhv http://apt.sw.be/redhat/el5/en/i386/rpmforge/RPMS/rpmforge-release-0.3.6-1.el5.rf.i386.rpm
	rpm -Uhv http://apt.sw.be/redhat/el5/en/x86_64/rpmforge/RPMS//rpmforge-release-0.3.6-1.el5.rf.x86_64.rpm

    EPEL:
	rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm

- Install git::

	yum install git

- Install python-setuptools::

	yum install python-setuptools

- Install syck YAML library (optional)::

    yum install syck-python

- Install simpleJSON library (optional)::

    yum install python-simplejson
    
- Download the latest gitosis-ng code::

	git clone git://github.com/joemiller/gitosis-ng.git

- Install gitosis-ng::

	cd gitosis-ng
	python setup.py install

- Create a 'git' user and home directory ('/home/git'.  Modify to suit your tastes)::
 
	adduser -d /home/git -m -s /bin/bash -c gitosis-ng -r git

- Next, we will import our SSH key and initialize the ``gitosis-ng``
  configuration.  Your key will become the first user in the ``gitosis-ng``
  system and a member of the ``gitosis-admin`` group::

	sudo -H -u git gitosis-init < id_rsa.pub

Modify the ``gitosis.conf`` config file
---------------------------------------
You should setup a few basic options in your ``gitosis.conf`` file as well as
get familiar with the process.

The ``gitweb=yes`` option is recommend for ``gitosis-ng`` as this will allow
your git users to ``list`` all repositories that they have either ``readonly``
or ``writeable`` access to.  This functionality can also be enabled on a
per-repository basis by placing a ``gitweb=yes`` option in the
``[repo repo-name]`` section of the ``gitosis.conf`` file.

- First, clone the special ``gitosis-admin.git`` repository from your ``gitosis-ng`` server::

	git clone git@YOUR_GIT_SERVER:gitosis-admin.git
	cd gitosis-admin

- Edit the gitosis.conf file.  In the ``[gitosis]`` section, add::

	gitweb=yes
	loglevel=ERROR

- Commit changes and push back to the server::

	git commit -a -m 'added new variables in global section'
	git push

Other resources
-----------------------
The installation process for ``gitosis-ng`` is basically identical to
installing ``gitosis``.  Here are some other great resources on
installing ``gitosis``:

- http://nfocipher.com/index.php?op=ViewArticle&articleId=12&blogId=1
- http://scie.nti.st/2007/11/14/hosting-git-repositories-the-easy-and-secure-way


Managing it
===========

Show available ``gitosis-ng`` commands
--------------------------------------

- Send the 'help' command via SSH::

    ssh git@YOUR_GIT_SERVER help

        add-repo        : Create new repository. Usage: 'add-repo repo_name'
        help            : Get list of available commands
        list            : Get detailed list of git repositories
        list-json       : Get detailed list of repositories in JSON format
        list-short      : Get simple list of git repositories
        list-yaml       : Get detailed list of repositories in YAML format

Adding new users
----------------

- Checkout the special ``gitosis-admin.git`` repo::

    git clone git@YOUR_GIT_SERVER:gitosis-admin.git

- Copy the user's ssh public key to the ``keydir`` directory::

    cp username.pub gitosis-admin/keydir/

- Commit and push back to the ``gitosis-ng`` server::

    cd gitosis-admin
    git commit -a -m 'added ssh pubkey for user: username'
    git push
    
Creating new repositories
-------------------------

There are actually two ways to create repositories, the ``gitosis``
way and the ``gitosis-ng`` way.  We'll cover the ``gitosis-ng``
way here.  See the ``README.orig.rst`` file for the ``gitosis`` way.

Any user may create a repository.  That user will automatically
be given ``writeable`` access to that repository.  At this time,
only admins can grant access to other users or groups by
checking out and modifying the ``gitosis.conf`` file::

    ssh git@git.azdigitalfarm.com add-repo myproject

        To /home/git/repositories/gitosis-admin.git
           22c1bd3..a06d3df  master -> master
        Created repository: myproject

        Next Steps:
          mkdir myproject
          cd myproject
          git init
          touch README
          git add README
          git commit -a -m 'first commit'
          git remote add origin git@GIT_SERVER_ADDRESS:myproject.git
          git push origin master

        Existing Git repo?
          cd myproject
          git remote add origin git@GIT_SERVER_ADDRESS:myproject.git
          git push origin master


Listing available repositories
------------------------------

Any user can list repositories that he has been given either ``readonly``
or ``writeable`` access on::

    ssh git@YOUR_GIT_SERVER list
        Repository  : myproject.git
         Initialized: no
         Your Access: read/write
         Owner      : jmiller
         URL        : 
         Description: 

         Repository  : otherproject.git
         Initialized: no
         Your Access: readonly
         Owner      : bsmith
         URL        : 
         Description: 

Granting access to repositories
-------------------------------

Only admins can grant access to repositories at this time by
modifying the ``gitosis.conf`` file.

``readonly`` and ``writeable`` (read/write) access can be granted
to individual users or groups.

Grant access to individual users
--------------------------------

- Checkout the special ``gitosis-admin.git`` repo::

    git clone git@YOUR_GIT_SERVER:gitosis-admin.git

- Create a ``[repo myproject]`` section if one does not exist already,
and grant access to individual users::

    [repo myproject]
    writeable = jdoe bsmith
    readonly = rjones

- Commit that change and push.

Grant access to an entire group
----------------------------------

- Checkout the special ``gitosis-admin.git`` repo

- Create a ``[group groupname]`` section in gitosis.conf, specify
the members, and grant access to repostories.  Example::

    [group myteam]
    members = jdoe
    writable = myproject
    readonly = otherproject

- Commit that change and push.


Using git-daemon
================

Anonymous read-only access to ``git`` repositories is provided by
``git-daemon``, which is distributed as part of ``git``. But
``gitosis`` will still help you manage it: setting ``daemon = yes`` in
your ``gitosis.conf``, either globally in ``[gitosis]`` or
per-repository under ``[repo REPOSITORYNAME]``, makes ``gitosis``
create the ``git-daemon-export-ok`` files in those repository, thus
telling ``git-daemon`` that publishing those repositories is ok.

To actually run ``git-daemon`` in Ubuntu, put this in
``/etc/event.d/local-git-daemon``:

.. include:: etc-event.d-local-git-daemon
   :literal:

For other operating systems, use a similar invocation in an ``init.d``
script, ``/etc/inittab``, ``inetd.conf``, ``runit``, or something like
that (good luck).

Note that this short snippet is not a substitute for reading and
understanding the relevant documentation.


Using gitweb
============

``gitweb`` is a CGI script that lets one browse ``git`` repositories
on the web. It is most commonly used anonymously, but you could also
require authentication in your web server, before letting people use
it. ``gitosis`` can help here by generating a list of projects that
are publicly visible. Simply add a section ``[repo REPOSITORYNAME]``
to your ``gitosis.conf``, and allow publishing with ``gitweb = yes``
(or globally under ``[gitosis]``). You should also set ``description``
and ``owner`` for each repository.

Here's a LightTPD_ config file snippet showing how to run ``gitweb``
as a CGI:

.. _LightTPD: http://www.lighttpd.net/

.. include:: lighttpd-gitweb.conf
   :literal:

And a simple ``gitweb.conf`` file:

.. include:: gitweb.conf
   :literal:

Note that this short snippet is not a substitute for reading and
understanding the relevant documentation.



Contact
=======

You can email the author of ``gitosis-ng`` at ``joeym@joeym.net``.

You can email the author of ``gitosis`` at ``tv@eagain.net``, or hop on
``irc.freenode.net`` channel ``#git`` and hope for the best.
