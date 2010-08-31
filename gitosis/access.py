import os, logging
from ConfigParser import NoSectionError, NoOptionError

from gitosis import group

def haveAccess(config, user, mode, path):
    """
    Map request for write access to allowed path.

    Note for read-only access, the caller should check for write
    access too.

    Returns ``None`` for no access, or a tuple of toplevel directory
    containing repositories and a relative path to the physical repository.
    """
    log = logging.getLogger('gitosis.access.haveAccess')

    log.debug(
        'Access check for %(user)r as %(mode)r on %(path)r...'
        % dict(
        user=user,
        mode=mode,
        path=path,
        ))

    basename, ext = os.path.splitext(path)
    if ext == '.git':
        log.debug(
            'Stripping .git suffix from %(path)r, new value %(basename)r'
            % dict(
            path=path,
            basename=basename,
            ))
        path = basename

    # if there is a '[repo foo]' section in the config, check its
    # own access list first before checking the group accesslists
    try:
        repo_acl = config.get('repo %s' % basename, mode)
        log.debug('repo_acl: %(repo_acl)r' % dict(repo_acl=repo_acl))
    except (NoSectionError, NoOptionError):
        repo_acl = []
    else:
        repo_acl = repo_acl.split()

    if user in repo_acl:
        mapping = path
        prefix = None
        try:
            prefix = config.get('gitosis', 'repositories')
        except (NoSectionError, NoOptionError):
            prefix = 'repositories'

        log.debug(
            'repo ACL Access ok for %(user)r as %(mode)r on %(path)r'
            % dict(user=user, mode=mode, path=path))

        return (prefix, mapping)
    else:
        log.debug(
            'no repo ACL for %(user)r as %(mode)r on %(path)r'
            % dict(user=user, mode=mode, path=path))
    
    # now check to see if the user belongs to a group that has access to
    # this repo
    for groupname in group.getMembership(config=config, user=user):
        try:
            repos = config.get('group %s' % groupname, mode)
        except (NoSectionError, NoOptionError):
            repos = []
        else:
            repos = repos.split()

        mapping = None

        if path in repos:
            log.debug(
                'Access ok for %(user)r as %(mode)r on %(path)r'
                % dict(
                user=user,
                mode=mode,
                path=path,
                ))
            mapping = path
        else:
            try:
                mapping = config.get('group %s' % groupname,
                                     'map %s %s' % (mode, path))
            except (NoSectionError, NoOptionError):
                pass
            else:
                log.debug(
                    'Access ok for %(user)r as %(mode)r on %(path)r=%(mapping)r'
                    % dict(
                    user=user,
                    mode=mode,
                    path=path,
                    mapping=mapping,
                    ))

        if mapping is not None:
            prefix = None
            try:
                prefix = config.get(
                    'group %s' % groupname, 'repositories')
            except (NoSectionError, NoOptionError):
                try:
                    prefix = config.get('gitosis', 'repositories')
                except (NoSectionError, NoOptionError):
                    prefix = 'repositories'

            log.debug(
                'Using prefix %(prefix)r for %(path)r'
                % dict(
                prefix=prefix,
                path=mapping,
                ))
            return (prefix, mapping)
