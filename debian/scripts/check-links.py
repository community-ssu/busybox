#!/usr/bin/python
#
# Check that the binaries for links BusyBox outputs and the ones
# in the packages *.links files match.
#
# Copyright (C) 2008 by Nokia Corporation
#
# Contact: Eero Tamminen <eero.tamminen@nokia.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301 USA

import os, sys

def add_links_from(filename, olditems):
    "read busybox.links file and return a list of binary names"
    newitems = {}
    existing = []
    print "-", filename
    for line in open(filename):
        line = line.strip()
        if not line:
            continue
        name = os.path.basename(line.split()[-1])
        if name in olditems and name not in newitems:
            # same package may symlink same name to different
            # places, but other packages may not
            existing.append(name)
        else:
            olditems[name] = filename
            newitems[name] = 1
    
    if existing:
        print "ERROR: following items were already in (some) previous links file:"
        for name in existing:
            print "-", name
        print "Re-run of create-control.py needed?"
        sys.exit(1)


def process_args(argv):
    links = {}
    bblinks = {}
    print "Checking:"
    add_links_from(argv[1], bblinks)
    for filename in argv[2:]:
        add_links_from(filename, links)
    
    missing = []
    for link in bblinks.keys():
        if link in links:
            del(links[link])
        else:
            missing.append(link)
    
    if missing:
        print "WARNING: links files for packages are missing following BB links:"
        for link in missing:
            print "-", link
        print "Are all these installed as alternatives?"
    
    if links:
        print "ERROR: BB links file doesn't contain following packages links:"
        for link in links.keys():
            print "- %s (in '%s')" % (link, links[link])
        print "Re-run of create-control.py needed?"
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        process_args(sys.argv)
    else:
	print """
Script to check that binary names in packages link files
match the list of binary names in the BB link file.

usage: %s <BB links file> <packages link files>
""" % os.path.basename(sys.argv[0])
	sys.exit(1)

