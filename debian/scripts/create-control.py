#!/usr/bin/python
#
# Output BusyBox source package debian/control file and
# relevant *.links & *.postist files for the binary packages,
# based on the Busybox configuration and Debian package
# mappings file.
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
#
# Notes:
# - If some package provide only alternatives, Busybox package
#   control file is set up to provide those and its postinst to
#   install the alternatives.  As they cannot conflict, there's
#   no need to put them into separate symlink packages

# source package, busybox and debug package descriptions
basepackages_info = """
Source: busybox
Priority: optional
Section: utils
Maintainer: Yauheni Kaliuta <yauheni.kaliuta@nokia.com>
Original-Maintainer: Debian Install System Team <debian-boot@lists.debian.org>
Original-Uploaders: Bastian Blank <waldi@debian.org>
Build-Depends: debhelper (>> 5), lsb-release, python, quilt
Standards-Version: 3.7.3

Package: busybox
Essential: yes
Architecture: any
Depends: ${shlibs:Depends}
Provides: %(provides)s
Replaces: %(replaces)s
Conflicts: %(conflicts)s
Description: Tiny utilities for small and embedded systems
 BusyBox combines tiny versions of many common UNIX utilities into a single
 small executable. It provides minimalist replacements for the most common
 utilities you would usually find on your desktop system (i.e., ls, cp, mv,
 mount, tar, etc.). The utilities in BusyBox generally have fewer options than
 their full-featured GNU cousins; however, the options that are included
 provide the expected functionality and behave very much like their GNU
 counterparts.
 .
 This package installs:
 - the BusyBox binary
 - symlinks for tools included into it that correspond to binaries
   in essential Debian packages
 - alternatives from packages that don't have anything else
 .
 Symlinks to other tools included into BusyBox which correspond to binaries
 in non-essential Debian packages are provided in separate symlink packages.
 Those package are split and named according to the corresponding Debian
 packages.

Package: busybox-dbg
Architecture: any
Depends: busybox (= ${binary:Version})
Section: devel
Description: Debug symbols for BusyBox
 Debug symbol file for BusyBox. BusyBox provides tiny utilities for small
 and embedded systems.
"""

# description for the busybox specific tools symlinks package
symlinksbusybox_info = """
Package: busybox-symlinks-busybox
Architecture: all
Depends: busybox (= ${binary:Version})
Description: BusyBox specific symlinks
 BusyBox symlinks for utilities without counterparts in Debian.
 These are in separate package because they aren't essentials
 (e.g. needed for system package upgrades).
"""

# descriptions for the other busybox symlinks packages
symlinksother_info = """
Package: busybox-symlinks-%s
Architecture: all
Depends: busybox (= ${binary:Version})
Provides: %s
Replaces: %s
Conflicts: %s
Description: BusyBox symlinks to provide '%s'
 BusyBox symlinks for utilities corresponding to '%s' package.
"""

# List of packages that are in Debian Lenny marked as essential:
# awk '/Package:/{pkg=$2} /Essential: yes/{printf("\"%s\",\n", pkg)}' < /var/lib/dpkg/status|sort
#
# Because we don't have "bash", but BusyBox provides "ash", I've set
# that as Essential (instead of Bash) and specifically divert "/bin/sh"
# in code below if that is included into Busybox links (in Ubuntu
# "dash" does same kind of divert).
#
# Some essential packages in Debian "provide" packages that in earlier
# Debian versions were in separate packages.  These aren't listed here
# because they're unnecessary:
# 
# * coreutils provides: fileutils, shellutils, textutils
#   -> no explicit dependencies for these in Lenny.  In Etch "latex2html"
#      requires "fileutils" without having "coreutils" as an alternative,
#      but that's a versioned dependency that wouldn't work with
#      BusyBox anyway
# 
# * util-linux provides: linux32, schedutils
#   -> these were separate packages still in Etch, but as nothing explicitly
#      depends on them in Etch or Lenny and Maemo BusyBox configuration
#      doesn't include binaries from Etch linux32 or schedutils, they
#      don't need to be declared
# 
# * grep provides: rgrep
#   -> there are no dependencies to "rgrep" in Etch or Lenny and as it
#      cannot even be enabled in BusyBox, it doesn't need to be declared
essentialpackages = (
    'ash',          # Maemo special case, see above
    'base-files',
    'base-passwd',
    'bash',
    'bsdutils',
    'coreutils',
    'debianutils',
    'diff',
    'dpkg',
    'e2fsprogs',
    'findutils',
    'grep',
    'gzip',
    'hostname',
    'login',
    'mktemp',
    'mount',
    'ncurses-base',
    'ncurses-bin',
    'perl-base',
    'schedutils',
    'sed',
    'sysvinit',
    'sysvinit-maemo',
    'sysvinit-utils',
    'tar',
    'util-linux'
)


import os, sys
stderr = sys.stderr.write

def error_exit(msg):
    "exit with given error message"
    sys.stderr.write("\nERROR: %s\n\n" % msg)
    sys.exit(1)

def check_file(filename, filetype):
    "exit if given filename doesn't exist or isn't a file"
    if os.path.isfile(filename):
        return
    error_exit("%s file '%s' doesn't exist!" % (filetype, filename))


def read_mappings(filename):
    """read Debian mappings file and return dicts for
    - package = [list of binaries]
    - binary = (package, [paths/alternative info])
    """
    check_file(filename, "Debian mappings")
    binaries = {}
    packages = {}
    for line in open(filename):
        line = line.strip()
        if (not line) or (line[0] == '#'):
            continue
        package, data = line.split(":")
	paths = data.strip().split()
	binary = os.path.basename(paths[0].strip())
	binaries[binary] = (package, paths)
        if package not in packages:
            packages[package] = []
        packages[package].append(binary)
    return packages, binaries


def read_links(filename):
    "read busybox.links file and return a list of binary names"
    check_file(filename, "links")
    items = []
    for line in open(filename):
        line = line.strip()
        if not line:
            continue
        items.append(os.path.basename(line))
    items.sort()
    return items


def read_config(filename):
    "read BusyBox config and return list of enabled applets"
    check_file(filename, "BusyBox config")
    applets = []
    for line in open(filename):
        if not line.startswith("CONFIG_"):
            continue
	if line.startswith("CONFIG_LFS"):
	    continue
        # stuff after CONFIG_
        config = line[7:].split('=')[0]
        if '_' in config:
            # BB applet names don't have '_'
            continue
        applets.append(config.lower())
    
    # remove busybox config crap
    if "debug" in applets:
        applets.remove("debug")
    if "prefix" in applets:
        applets.remove("prefix")

    # some applets provide multiple binary symlinks, fix
    if "swaponoff" in applets:
        applets.remove("swaponoff")
        applets.append("swapoff")
        applets.append("swapon")
    if "ifupdown" in applets:
        applets.remove("ifupdown")
        applets.append("ifdown")
        applets.append("ifup")
    
    applets.sort()
    return applets


def tools2packages(tools, binaries):
    """match BB tools to Debian binaries and return list of
       corresponding packages.  Assert that each binary is
       associated to some package ("sh" is special case)."""
    missing = []
    packages = {}
    for tool in tools:
        if tool in binaries:
            package = binaries[tool][0]
            if package not in packages:
                packages[package] = []
            packages[package].append(tool)
        # /bin/sh is special case
        elif tool != "sh":
            missing.append(tool)
    if missing:
        stderr("\nERROR: following tools didn't belong to any mapped package:\n")
        for name in missing:
            stderr("- %s\n" % name)
        stderr("Update either %s::read_config() code or Debian mappings file!\n\n" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    return packages


def check_packages(packages, bbpackages):
    "warn if packages provided by BB are missing tools that BB could include"
    missing = {}
    for package in bbpackages.keys():
        if package == "busybox":
            # ignore busybox specific tools
            continue
        for binary in packages[package]:
            if binary not in bbpackages[package]:
                if package not in missing:
                    missing[package] = []
                missing[package].append(binary)
    for package in missing.keys():
        stderr("\nWARNING: '%s' package could include also:\n" % package)
        for binary in missing[package]:
            stderr("  - %s\n" % binary)


def collect_packages(bbpackages, tools, binaries):
    "return lists of packages BB conflicts with, provides and symlinks"
    base = {} # directly to Busybox package
    extras = {} # alternatives for Busybox package
    symlinks = {} # symlinks/alteratives for symlink packages

    for package, tools in bbpackages.items():
        # package is essential -> goes to busybox itself
        if package in essentialpackages:
            base[package] = tools
            continue

        allalternatives = True
        # check whether all tools from given pkg are alternatives
        for tool in tools:
            toolinfo = binaries[tool][1]
            if len(toolinfo) < 2 or toolinfo[1] != "alternative":
                allalternatives = False

        if allalternatives:
            # only alternatives -> can be provided by busybox itself
            extras[package] = tools
        else:
            # otherwise a separate symlinks package
            symlinks[package] = tools
     
    return base, extras, symlinks


def collect_links_alternatives(tools, binaries, links, postinst):
    "go through given packages and set/update links & postinst contents"
    for tool in tools:
        toolinfo = binaries[tool][1]
        count = len(toolinfo)
        if count > 1 and toolinfo[1] == "alternative":
            target = "/bin/busybox"
            link = toolinfo[0]
            if count > 2:
                priority = int(toolinfo[2])
                if count > 3:
                    # alternative having different name than BB symlink
                    # means that alternative needs to point to BB symlink
                    # instead of directly to BB so that BB knows which
                    # applet to use for the alternative (e.g. pager):
                    #	tool -> altlink -> target -> busybox
                    links.append(link)
                    target = '/' + link
                    link = toolinfo[3]
                    tool = os.path.basename(link)
            else:
                priority = 1
            postinst.append(('/' + link, tool, target, priority))
        else:
            for link in toolinfo:
                links.append(link)


def write_links(package, links):
    "write given package links file"
    if not links:
        return
    name = "%s.links" % package
    print "-", name
    linksfile = open(name, "w")
    if not linksfile:
        error_exit("opening/writing package '%s' links file failed")
    for link in links:
        linksfile.write("bin/busybox %s\n" % link)
    linksfile.close()


def write_alternatives(package, alternatives, diverts=[]):
    "write given alternatives updates for given package postinst/prerm files"
    if not (alternatives or diverts):
        return
    
    name = "%s.postinst" % package
    print "-", name
    postinst = open(name, "w")
    if not postinst:
        error_exit("opening/writing package '%s' postinst file failed")
    
    postinst.write("#!/bin/sh\nset -e\n")
    for link,tool,target,priority in alternatives:
        postinst.write("update-alternatives --install %s %s %s %d\n" % (link, tool, target, priority))
    for divert in diverts:
        # Note: as dpkg-divert --rename doesn't work as described
        # in the manual page, it's not used here
        postinst.write("dpkg-divert --package %s --add %s\n" % (package, divert))
    postinst.close()
    
    name = "%s.prerm" % package
    print "-", name
    prerm = open(name, "w")
    if not prerm:
        error_exit("opening/writing package '%s' prerm file failed")
    
    prerm.write("#!/bin/sh\nset -e\n")
    for link,tool,target,priority in alternatives:
        prerm.write("update-alternatives --remove %s %s\n" % (tool, target))
    for divert in diverts:
        prerm.write("dpkg-divert --package %s --remove %s\n" % (package, divert))
    prerm.close()


def create_links_alternatives(bbpackages, bblinks, binaries):
    """generate .postinst files for tools needing alternatives,
    and .links files for required symlinks. If package would include
    only alternatives, just add them to busybox package as provides
    (without conflicts/replaces).
    
    Return lists of packages going to busybox package with which
    it needs to conflict with, ones it can just provide (as they're
    handled as alternatives), and packages that would contain
    separate non-essential symlink packages."""

    base, extras, symlinks = collect_packages(bbpackages, bblinks, binaries)
    
    links = []
    alternatives = []
    for package,tools in base.items():
        collect_links_alternatives(tools, binaries, links, alternatives)
    # add extra alternatives to alternatives
    for package,tools in extras.items():
        collect_links_alternatives(tools, binaries, None, alternatives)
    if "bin/sh" in links:
        # /bin/sh is special case as in Maemo, BusyBox should be /bin/sh.
        # In Debian it's linked by Bash.  In Ubuntu /bin/sh is diverted
        # by Dash (by default), so let's do divert here too.
        divert = ["/bin/sh"]
    else:
        divert = []
    write_alternatives("busybox", alternatives, divert)
    links.sort() # nicer to read/verify
    write_links("busybox", links)

    for package,tools in symlinks.items():
        links = []
        alternatives = []
        collect_links_alternatives(tools, binaries, links, alternatives)
        pkgname = "busybox-symlinks-%s" % package
        write_alternatives(pkgname, alternatives)
        write_links(pkgname, links)

    return base.keys(), extras.keys(), symlinks.keys()


def create_control(base, extraprovides, symlinks):
    "generate busybox control file based on given packages lists"
    # add same list of packages for provides, replaces & conflicts
    args = {}
    base.sort()
    args['conflicts'] = ", ".join(base)
    args['replaces'] = args['conflicts']
    if extraprovides:
        # busybox provides some extra packages with alternatives
        provides = base + extraprovides
        provides.sort()
        args['provides'] = ", ".join(provides)
    else:
        args['provides'] = args['conflicts']
    
    print "- control"
    control = open("control", "w")
    if not control:
        error_exit("opening/writing package 'control' file failed")
    control.write(basepackages_info % args)

    # special case package with it's own description
    if "busybox" in symlinks:
        symlinks.remove("busybox")
        control.write(symlinksbusybox_info)

    # other symlink packages descriptions
    symlinks.sort()
    for package in symlinks:
        args = 6*(package,)
        control.write(symlinksother_info % args)
    control.close()


def process_args(argv):
    if len(sys.argv) == 4 and sys.argv[1] in ("-c", "-l"):
        print "\nPARSING..."
        if sys.argv[1] == "-l":
            tools = read_links(sys.argv[2])
        else:
            tools = read_config(sys.argv[2])
	packages, binaries = read_mappings(sys.argv[3])
        bbpackages = tools2packages(tools, binaries)
        check_packages(packages, bbpackages)
        print '\n', 66*'-', "\n\nWRITING:"
        base, extras, symlinks = create_links_alternatives(bbpackages, tools, binaries)
        create_control(base, extras, symlinks)
        print
    else:
	script = os.path.basename(sys.argv[0])
	print """
Outputs BusyBox Debian package control/links/postinst/prerm
files based on the input files.

usage: %s <-c bb.config|-l bb.links> <mappings file>

Example of first invocation using BusyBox config file:
	%s -c config.maemo debian-mappings.txt

Example of later iterations using the BusyBox generated symlinks file:
	%s -l busybox.links debian-mappings.txt
""" % (script, script, script)
	sys.exit(1)

if __name__ == "__main__":
    process_args(sys.argv)
