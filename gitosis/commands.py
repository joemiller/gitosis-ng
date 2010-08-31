#
# Implement helpful commands that can be sent over SSH.
#
# The list commands will mostly follow the same guidelines as gitweb.
# In order for a repository to be shown, it must be viewable by gitweb
# and the user must have either readonly or writeable access.
#
#   gitosis.conf:
#      [gitosis]
#      gitweb = yes
#
#      [repo myproject]
#      gitweb = yes
#      owner = joe miller
#      url = http://wiki.host.com/myproject
#      description = This is my project
#
#   $ ssh git@git.host.com help
#     help            : Get list of available commands
#     list            : Get detailed list of git repositories
#     list-json       : Get detailed list of repositories in JSON format
#     list-short      : Get a short list of git repositories
#     list-yaml       : Get detailed list of repositories in YAML format
#
#  $ ssh git@git.host.com list
#    Repository  : myproject.git
#    Owner       : joe miller
#    URL         : http://wiki.host.com/myproject
#    Description : This is my project
#
# joe miller, <joeym@joeym.net>, 8/26/2010
#

import sys, os, shutil, logging

from ConfigParser import NoSectionError, NoOptionError

from gitosis import util
from gitosis import access
from gitosis import config
from gitosis import repository

log = logging.getLogger('gitosis.commands')

COMMAND_LIST = {
    'help': "Get list of available commands",
    'list': "Get detailed list of git repositories",
    'list-short': "Get simple list of git repositories",
    'list-json': "Get detailed list of repositories in JSON format",
    'list-yaml': "Get detailed list of repositories in YAML format",
    'add-repo': "Create new repository. Usage: 'add-repo repo_name'",
}

def help():
    ret = ''
    for command, desc in sorted(COMMAND_LIST.items()):
        ret += "%-15s : %s\n" % (command, desc)
    return ret

def dispatch(config, user, command, args):
    if command == 'list':
        return print_long_repo_list(config, user)
    elif command == 'list-short':
        return print_short_repo_list(config, user)
    elif command == 'list-json':
        return json_repo_list(config, user)
    elif command == 'list-yaml':
        return yaml_repo_list(config, user)
    elif command == 'add-repo':
        return add_repo(config, user, args)
    elif command == 'help':
        return help()

def print_long_repo_list(config, user):
    repos = get_repo_list(config, user)

    ret = ''
    for repo, vals in sorted(repos.items()):
        ret += "\n"
        ret += "Repository  : %s\n" % repo
        ret += " Initialized: %s\n" % ("no","yes")[vals['initialized']]
        ret += " Your Access: %s\n" % vals['acl']
        ret += " Owner      : %s\n" % vals['owner']
        ret += " URL        : %s\n" % vals['url']
        ret += " Description: %s\n" % vals['description']
    return ret

def print_short_repo_list(config, user):
    repos = get_repo_list(config, user)

    ret = ''
    for repo, vals in sorted(repos.items()):
        ret += "%s\n" % repo
    return ret

def json_repo_list(config, user):
    try:
        import simplejson as json
        repos = get_repo_list(config, user)
        return json.dumps(repos, indent=4)
    except ImportError:
        log.error("The 'simplejson' python module is not installed")

def yaml_repo_list(config, user):
    try:
        import ydump
        repos = get_repo_list(config, user)
        return ydump.dump(repos)
    except ImportError:
        log.error("The 'syck' python module is not installed")

def get_repo_list(config, user):
    """ get list of repos and metadata, return as a dictionary """

    repositories = util.getRepositoryDir(config)

    repos = {}

    try:
        global_enable = config.getboolean('gitosis', 'gitweb')
    except (NoSectionError, NoOptionError):
        global_enable = False

    for section in config.sections():
        l = section.split(None, 1)
        type_ = l.pop(0)
        if type_ != 'repo':
            continue
        if not l:
            continue

        try:
            enable = config.getboolean(section, 'gitweb')
        except (NoSectionError, NoOptionError):
            enable = global_enable

        if not enable:
            continue

        name, = l
        owner = ""
        url = ""
        acl = ""
        initialized = False
        descr = ""

        if not os.path.exists(os.path.join(repositories, name)):
            namedotgit = '%s.git' % name
            if os.path.exists(os.path.join(repositories, namedotgit)):
                name = namedotgit

        if os.path.exists(os.path.join(repositories, name)):
            initialized = True

        if initialized == False:
            name = '%s.git' % name
    
        # check that user has either 'writeable' or 'readonly' access
        # otherwise don't show them this repo at all
    
        has_write = access.haveAccess(config, user, 'writeable', name)
        if has_write == None:
            # try misspelling 'writable'
            has_write = access.haveAccess(config, user, 'writable', name)

        has_read = access.haveAccess(config, user, 'readonly', name)

        if has_write == None and has_read == None:
            log.debug("has neither read nor write!")
            continue

        if has_write:
            acl = "read/write"
        elif has_read:
            acl = "readonly"

        # get 'owner = ' from [repo foo]
        try:
            owner = config.get(section, 'owner')
        except (NoSectionError, NoOptionError):
            pass

        # get 'url = ' from [repo foo]
        try:
            url = config.get(section, 'url')
        except (NoSectionError, NoOptionError):
            pass

        # get 'description = ' from [repo foo]
        try:
            descr = config.get(section, 'description')
        except (NoSectionError, NoOptionError):
            pass

        log.debug('section=%(section)r desc=%(description)r' % dict(section=section, description=descr))
        repos[name] = { 'owner': owner,
                'url': url, 
                'acl': acl,
                'initialized': initialized,
                'description': descr }
    return repos


def add_repo(config, user, args):
    # strip '.git' from repo
    repo = args
    if repo.endswith('.git'):
        repo = repo[:-4]

    section = "repo " + repo
    if config.has_section(section):
        return("repository '%s' already exists\n" % repo)

    config.add_section(section)
    config.set(section, 'url', "")
    config.set(section, 'owner', user)
    config.set(section, 'description', "")
    config.set(section, 'writeable', user)

    try:
        update_config_file(config, user, repo)
    except Exception, e:
        return "Failed to create repository (%s): %s\n" % (repo, e)
    else:
        msg = "Created repository: %s\n" % repo
        msg += "\nNext Steps:\n"
        msg += "  mkdir %s\n" % repo
        msg += "  cd %s\n" % repo
        msg += "  git init\n"
        msg += "  touch README\n"
        msg += "  git add README\n"
        msg += "  git commit -a -m 'first commit'\n"
        msg += "  git remote add origin git@GIT_SERVER_ADDRESS:%s.git\n" % repo
        msg += "  git push origin master\n"
        msg += "\nExisting Git repo?\n"
        msg += "  cd %s\n" % repo
        msg += "  git remote add origin git@GIT_SERVER_ADDRESS:%s.git\n" % repo
        msg += "  git push origin master\n"
        return msg

def update_config_file(config, user, repo):
    admin_repository = os.path.join( 
                        util.getRepositoryDir(config),
                        'gitosis-admin.git')

    export = os.path.join(admin_repository, 'gitosis-clone-%d' % os.getpid())
    conf_file = os.path.join(export, 'gitosis.conf')
    tmp_conf_file = "%s.tmp.%d" % (conf_file, os.getpid())

    repository.clone(git_dir=admin_repository, path=export)

    shutil.copy(conf_file, tmp_conf_file)
    fp = file(tmp_conf_file, 'r+')
    config.update_file(fp)
    fp.close()
    shutil.move(tmp_conf_file, conf_file)

    repository.commit(
        git_dir = export,
        author = "Gitsosis Admin <%s>" % user,
        msg = "User %s created repository %s" % (user, repo),
        )
    shutil.rmtree(export)

# TODO:
# * more commands:
#  set-repo <repo-name> <key> <value>
#      eg:  set-repo myproject url http://wiki.example.com/myproject
#  add-user ?
#  del-repo (maybe not, kinda dangerous)
