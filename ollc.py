#!/usr/bin/env python

## Cross-version imports. This allows to write python3-like code that
## can be run by a python2 interpreter.
## See http://python-future.org/imports.html
from __future__ import absolute_import, division, print_function

import os
import sys
import subprocess

## subprocess.DEVNULL is defined only in python3. If we fail to import it
## (i.e. we are on python2) we define it manually.
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

try:
    # py3k
    from configparser import ConfigParser
except ImportError:
    # python 2
    from ConfigParser import ConfigParser

## This is a mapping between command line options and the name and section with
## which they are saved in the configuration file.
OPTIONS = {'--rev': {'section': 'repository',
                     'option':  'revision'}}

## The upstream repository from which we want to clone OpenLilyLib
UPSTREAM_REPOSITORY = 'https://github.com/openlilylib/openlilylib.git'

class OpenLilyLibRepo(object):
    """The (local) repository of OpenLilyLib code.

    This class represents the local mirror of the upstream OpenLilyLib
    repository. It provides facilities to clone from upstream, pull changes and
    checkout specific revisions.

    To create a new object of this class use, for instance

        OpenLilyLibRepo.at_revision('master')
    """

    @staticmethod
    def at_revision(revision):
        """Instantiate a repository class at the specified revision.

        If the repository does not exist it is cloned. If the revision is
        already present in the repository, it is checked out. If the repository
        does not contain the revision, the latest changes are pulled from
        upstream.

        Branch names are considered valid as arguments to the function: they
        will always trigger a pull from upstream.
        """
        repo = OpenLilyLibRepo()
        if not repo.has_revision(revision):
            print("Updating OpenLilyLib repository information")
            repo.clone_if_needed()
            ## Checkout master to avoid errors due to a pull in
            ## detached head state.
            repo.checkout('master')
            repo.pull()
        repo.checkout(revision)
        return repo

    def __init__(self):
        self.local_repo = os.path.expanduser('~/.oll/openlilylib')
        self.local_git_dir = os.path.join(self.local_repo, '.git')
        self.remote_repo = UPSTREAM_REPOSITORY

    def git(self, args, capture_output=False):
        """Runs git on the local OpenLilyLib clone. Set capture_output to True to
        have the output of the git command returned as a string
        """
        command = ['git']
        command.append('--work-tree={}'.format(self.local_repo))
        command.append('--git-dir={}'.format(self.local_git_dir))
        command.extend(args)
        out_mode = subprocess.PIPE if capture_output else DEVNULL
        process = subprocess.Popen(command,
                                   stdout=out_mode,
                                   stderr=out_mode,
                                   close_fds=True)
        output, _ = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                'Command exited with error code {0}:\n$ {1}'.format(
                    process.returncode,
                    ' '.join(command)))
        else:
            return output

    def has_revision(self, revision):
        """Return true if the given revision is in the `rev-list` and
        the repository exists."""
        if not self.has_clone():
            return False
        revlist = self.git(['rev-list', '--all'], capture_output=True)\
                      .decode().split('\n')
        return revision in revlist

    def has_clone(self):
        """Return true if the repository has been cloned."""
        return os.path.isdir(self.local_repo)

    def clone(self):
        """Clones the repository from github."""
        print("Cloning the repository")
        subprocess.call(['git',
                         'clone',
                         '--progress',
                         self.remote_repo,
                         self.local_repo])

    def clone_if_needed(self):
        """Clones the repository only if needed."""
        if not self.has_clone():
            self.clone()

    def pull(self):
        """Pull the latest changes from upstream."""
        self.git(['pull'])

    def checkout(self, revision):
        """Checkout the given revision"""
        self.git(['checkout', revision])

    def current_revision(self):
        """Returns the current revision as given by `git rev-parse`"""
        return self.git(['rev-parse', 'HEAD'],
                        capture_output=True).decode().strip()

    def include_dirs(self):
        """Return the include directories to be added to lilypond's path."""
        return [self.local_repo,
                os.path.join(self.local_repo, 'ly')]


class LilypondCommand(object):
    """Wrapper for the lilypond command."""

    def __init__(self, config):
        self.oll_revision = config['repository']['revision']
        self.oll_repo = OpenLilyLibRepo.at_revision(self.oll_revision)
        self.oll_revision = self.oll_repo.current_revision()
        print("Using OpenLilyLib revision", self.oll_revision)
        self.persist_config()

    @staticmethod
    def config_file():
        """The path to the configuration file in the local directory.

        Returns the name of the configuration file in the directory in which
        this script is executed
        """
        return os.path.join(os.curdir, 'ollc.conf')

    @staticmethod
    def load_config(arglist):
        """Loads the configuration for this command.

        In order of precedence:

         - Command line
         - Configuration file
         - Defaults
        """

        # Define defaults
        config = {
            'repository': {'revision': 'master'}
        }

        # Load from file
        if os.path.isfile(LilypondCommand.config_file()):
            config_file = ConfigParser()
            config_file.read(LilypondCommand.config_file())
            for s in config_file.sections():
                if s not in config:
                    config[s] = dict()
                for k in config_file.options(s):
                    config[s][k] = config_file.get(s, k)

        # Load from argument list
        for k in OPTIONS.keys():
            if k in arglist:
                val = arglist[arglist.index(k) + 1]
                config[OPTIONS[k]['section']][OPTIONS[k]['option']] = val

        return config

    @staticmethod
    def from_config(arglist):
        """Factory method to create a command from the given argument list."""
        config = LilypondCommand.load_config(arglist)
        return LilypondCommand(config)

    def persist_config(self):
        """Save the current command configuration to 'self.config_file()'"""
        with open(LilypondCommand.config_file(), 'w') as out:
            config = ConfigParser()
            config.add_section('repository')
            config.set('repository', 'revision', self.oll_revision)
            config.write(out)

    @staticmethod
    def filter_lily_args(arglist):
        """Filter the given argument list, retaining only the arguments to
        be passed to Lilypond.

        Removes options declared in OPTIONS (along with their arguments).
        """
        filtered = list(arglist)
        for opt in OPTIONS.keys():
            if opt in filtered:
                idx = filtered.index(opt)
                # delete the option
                del filtered[idx]
                # delete the value (it's the same index because
                # the list length changes)
                del filtered[idx]
        return filtered

    def run(self, args):
        """Runs lilypond with the given arguments, adding to the include
        path the relevant directories of the OpenLilyLib repository."""
        command = ['lilypond']
        for include_dir in self.oll_repo.include_dirs():
            command.extend(['-I', include_dir])
        arguments = LilypondCommand.filter_lily_args(args)
        command.extend(arguments)
        subprocess.call(command)

def main():
    arguments = sys.argv[1:]
    lilycmd = LilypondCommand.from_config(arguments)
    lilycmd.run(arguments)

if __name__ == "__main__":
    main()
