`ollc` - an OpenLilyLib wrapper
===============================

`ollc` stands for OpenLilyLib Compiler, and is a simple script
wrapping the `lilypond` command.
[OpenLilyLib](https://github.com/openlilylib/openlilylib) is "a place
to store and collaborate on LilyPond tools - snippets, templates,
extensions".

Since OpenLilyLib is still evolving, it is desirable for scores using
it to refer to a fixed "snapshot", in order to avoid problems deriving
from breaking changes. Thus, `ollc` provides a way to

  - Automatically clone the OpenLilyLib repository, if needed.
  - Consistently reuse the same OpenLilyLib version in the same
	same score.
  - Include the appropriate directories in lilypond's search path.

Installation
------------

Just clone this repository somewhere

	$ cd ~/programs
	$ git clone https://github.com/Cecca/ollc.git

And then link (or copy) the `ollc` script somewhere in your path

    $ ln -s ~/programs/ollc/ollc ~/bin/ollc

Tutorial
--------

Suppose you are working on a score in directory `~/scores/score` with
a single file `main.ly`.

	$ cd ~/scores/score
	$ ls
	main.ly

You can compile the score using `ollc` by issuing the following command

	$ ollc main.ly
	Updating OpenLilyLib repository information
	Using OpenLilyLib revision 4c1236d0806fae8c8ce74a16ec5cf50f329c1cef
	GNU LilyPond 2.18.2
	Processing `main.ly'
	Parsing...
	Interpreting music...
	Preprocessing graphical objects...
	Finding the ideal number of pages...
	Fitting music on 1 page...
	Drawing systems...
	Layout output to `main.ps'...
	Converting to `./main.pdf'...
	Success: compilation successfully completed

This command will clone, only the first time, the OpenLilyLib
repository in a predefined location (`~/.oll/openlilylib`), and will
invoke `lilypond` adding to the include path the relevant OpenLilyLib
directories. Moreover, the program is telling you that the revision of
OpenLilyLib being included is
`4c1236d0806fae8c8ce74a16ec5cf50f329c1cef`.

Along with the usual output files, you will notice a new file, called
`ollc.conf`, that stores the aforementioned revision id.

	$ ls 
	main.ly  main.pdf  ollc.conf
	$ cat ollc.conf 
	[repository]
	revision = 4c1236d0806fae8c8ce74a16ec5cf50f329c1cef

This information will be used in subsequent runs of the program to
compile the score against the _exact same_ version of
OpenLilyLib. This way you can safely use different OpenLilyLib
versions in different scores.

If, at some point, you want to update to the latest version of
OpenLilyLib in order to get some new features, all you have to do is
to call `ollc` again with the `--rev` option

	$ ollc --rev master main.ly
	Updating OpenLilyLib repository information
	Using OpenLilyLib revision 049ecdd5762c76573f5c58ae45db834f4be44f40
	GNU LilyPond 2.18.2
	Processing `main.ly'
	Parsing...
	Interpreting music...
	Preprocessing graphical objects...
	Finding the ideal number of pages...
	Fitting music on 1 page...
	Drawing systems...
	Layout output to `main.ps'...
	Converting to `./main.pdf'...
	Success: compilation successfully completed

This will instruct `ollc` to pull the latest changes from upstream,
more specifically form the `master` branch. Now the information stored
in `ollc.conf` has been updated too

	$ cat ollc.conf
	[repository]
	revision = 049ecdd5762c76573f5c58ae45db834f4be44f40

hence all subsequent runs will use this new version of OpenLilyLib.

Usage
-----

	ollc [--rev REV] [lily-opts] file.ly

The `ollc` command accepts all the standard lilypond options that are,
in fact, passed to lilypond itself without any modification. `ollc`
supports an additional option, `--rev`, to specify the revision of
OpenLilyLib we want to use:

 - `ollc --rev master` will use the latest revision in `master`.
 - `ollc --rev some-branch` will use the latest revision in branch
    `some-branch`.
 - `ollc --rev 8f93b25` will use revision `8f93b25` of OpenLilyLib.

You can omit the `--rev` option. In this case, `ollc` will look inside
the current directory: if there is a file called `ollc.conf`
containing information about the revision used the last time the score
was compiled using `ollc`, then that revision is used; otherwise, the
latest revision found in the `master` branch from upstream will be
used.

In any case, after it is invoked, `ollc` will create (or update) the
file `ollc.conf` in the current working directory.
