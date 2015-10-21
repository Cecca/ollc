#!/usr/bin/env python

## Cross-version stuff
from __future__ import absolute_import, division, print_function
## FIXME see how to import this
#from builtins import *

import subprocess
import os
import sys
## TODO: Investigate YAML (needs additional dependency)
import json

OPTIONS = {'--rev': 'openlilylib_revision'}

class OpenLilyLibRepo(object):
    def __init__(self):
        self.local_repo = os.path.expanduser('~/.oll/openlilylib')
        self.local_git_dir = os.path.join(self.local_repo, '.git')
        self.remote_repo = 'https://github.com/openlilylib/openlilylib.git'

    def git(self, args, git_dir=None, capture_output=False):
        command = ['git']
        if git_dir is not None:
            command.append('--git-dir={}'.format(git_dir))
        command.extend(args)
        out_mode = subprocess.PIPE if capture_output else subprocess.STDOUT
        process = subprocess.Popen(command, stdout=out_mode)
        output, _ = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                'Command exited with error code {0}:\n$ {1}'.format(
                    process.returncode,
                    ' '.join(command)))
        else:
            return output

    def has_clone(self):
        return os.path.isdir(self.local_repo)

    def clone(self):
        print("Cloning the repository")
        self.git(['clone',
                  '--progress',
                  self.remote_repo,
                  self.local_repo])

    def clone_if_needed(self):
        if not self.has_clone():
            self.clone()

    def pull(self):
        self.git(['pull'], git_dir=self.local_git_dir)

    def checkout(self, revision):
        self.git(['checkout', revision], git_dir=self.local_git_dir)

    def current_revision(self):
        return self.git(['rev-parse', 'HEAD'],
                        git_dir=self.local_git_dir, capture_output=True)

    def include_dirs(self):
        return [self.local_repo,
                os.path.join(self.local_repo, 'ly')]


class LilypondCommand(object):

    def __init__(self, config):
        self.oll_revision = config['openlilylib_revision']
        self.oll_repo = OpenLilyLibRepo()
        self.oll_repo.clone_if_needed()
        #self.oll_repo.pull()
        self.oll_repo.checkout(self.oll_revision)
        self.oll_revision = self.oll_repo.current_revision()
        print("Using OpenLilyLib revision",
              self.oll_revision)
        self.persist_config()

    @staticmethod
    def config_file():
        return os.path.join(os.curdir, '.ollc.json')

    @staticmethod
    def load_config(arglist):
        # Define defaults
        config = {
            'openlilylib_revision': 'master'
        }

        # Load from file
        if os.path.isfile(LilypondCommand.config_file()):
            with open(LilypondCommand.config_file(), 'r') as conf_f:
                json_conf = json.load(conf_f)
                for k in json_conf.keys():
                    config[k] = json_conf[k]

        # Load from argument list
        for k in OPTIONS.keys():
            if k in arglist:
                val = arglist[arglist.index(k) + 1]
                config[OPTIONS[k]] = val

        return config

    @staticmethod
    def from_config(arglist):
        config = LilypondCommand.load_config(arglist)
        LilypondCommand(config)

    def persist_config(self):
        with open(LilypondCommand.config_file(), 'w') as out:
            json.dump({'openlilylib_revision': self.oll_revision}, out)

    def run(self, args):
        command = ['lilypond']
        for include_dir in self.oll_repo.include_dirs():
            command.extend(['-I', include_dir])
        command.extend(args)
        subprocess.call(command)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    lilycmd = LilypondCommand.from_config(arguments)
    lilycmd.run(arguments)
