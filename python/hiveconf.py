#
# Copyright (C) 2003 by Cendio Systems
# Author: Peter Astrand <peter@cendio.se>
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import urllib2
import urlparse
import os
import string
import glob
import getopt

class DebugWriter:
    def __init__(self, debug):
        self.debug = debug
    
    def write(self, data):
        if self.debug:
            sys.stderr.write(data)

debugw = DebugWriter(debug=0)


class IndentPrinter:
    def __init__(self):
        self.indent = 0
        self.line_indented = 0

    def write(self, data):
        if self.indent and not self.line_indented:
            sys.stderr.write(" " * self.indent)
            self.line_indented = 1
        sys.stderr.write(data)
        if data.find("\n") != -1:
            self.line_indented = 0

    def change(self, val):
        self.indent += val
        

class Error(Exception): pass
class NoSuchParameterError(Error): pass
class NoSuchFolderError(Error): pass
class NoSuchObjectError(Error): pass
class ObjectExistsError(Error): pass
class InvalidObjectError(Error): pass
class BadBoolFormat(Error): pass
class BadIntegerFormat(Error): pass
class BadFloatFormat(Error): pass
class BadBinaryFormat(Error): pass
class BadListFormat(Error): pass
class ReadOnlySource(Error): pass
    
class SyntaxError(Error):
    def __init__(self, linenum):
        self.linenum = linenum

    def __str__(self):
        return "Bad line %d" % self.linenum

#
# Utility functions
#

def path2comps(path):
    # Remove first slash
    if path[0] == "/":
        path = path[1:]

    # Remove last slash
    if path[-1] == "/":
        path = path[:-1]
    
    return path.split("/")

def comps2path(comps):
    result = ""
    for component in comps:
        result += "/" + component
    return result

def fixup_url(url):
    """Change url slightly, so that urllib can be used for POSIX paths"""
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    if not scheme:
        scheme = "file"

    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


#
# End of utility functions
#

class NamespaceObject:
    pass


class Parameter(NamespaceObject):
    def __init__(self, value, source, sectionname, paramname):
        self.value = value
        # URL that this parameter was read from
        self.source = source
        self.sectionname = sectionname
        # FIXME: The class probably shouldn't know about it's own name.
        self.paramname = paramname

    #
    # Primitive data types, get operations
    #
    def get_string(self):
        """Get value as string"""
        return self.value

    def get_bool(self):
        """Get boolean value"""
        try:
            return self._string2bool(self.value)
        except ValueError:
            raise BadBoolFormat()
    
    def get_integer(self):
        """Get integer value"""
        try:
            return int(self.value)
        except ValueError:
            raise BadIntegerFormat()

    def get_float(self):
        """Get float value"""
        try:
            return float(self.value)
        except ValueError:
            raise BadFloatFormat()

    def get_binary(self):
        """Get binary value"""
        try:
            self._hexascii2string(self.value)
        except ValueError:
            raise BadBinaryFormat()

    #
    # Primitive data types, set operations
    #
    def set_string(self, new_value):
        """Set string value"""
        u = HiveFileUpdater(self.source)
        u.change_parameter(self.sectionname, self.paramname, new_value)

    def set_bool(self, new_value):
        """Set bool value"""
        self.set_string(self._bool2string(new_value))

    def set_integer(self, new_value):
        self.set_string(str(new_value))

    def set_float(self, new_value):
        self.set_string(str(new_value))

    def set_binary(self, new_value):
        self.set_string(self._string2hexascii(new_value))

    #
    # Compound data types, get operations
    #
    def get_string_list(self):
        return self.value.split()

    def get_bool_list(self):
        return map(self._string2bool, self.value.split())

    def get_integer_list(self):
        return map(int, self.value.split())

    def get_float_list(self):
        return map(float, self.value.split())

    def get_binary_list(self):
        return map(self._hexascii2string, self.value.split())

    #
    # Compound data types, set operations
    #
    def set_string_list(self, new_value):
        self.set_string(string.join(new_value))
    
    def set_bool_list(self, new_value):
        self.set_string_list(map(self._bool2string, new_value))

    def set_integer_list(self, new_value):
        self.set_string_list(map(str, new_value))

    def set_float_list(self, new_value):
        self.set_string_list(map(str, new_value))

    def set_binary_list(self, new_value):
        self.set_string_list(map(self._string2hexascii, new_value))

    #
    # Internal methods
    #
    def _bool2string(self, value):
        """Convert a Python bool value to 'true' or 'false'"""
        return value and "true" or "false"
        
    def _string2hexascii(self, s):
        """Convert string to hexascii"""
        result = ""
        for char in s:
            result += "%02x" % ord(char)
        return result

    def _hexascii2string(self, s):
        """Convert hexascii to string"""
        result = ""
        for x in range(len(s)/2):
            pair = s[x*2:x*2+2]
            val = int(pair, 16)
            result += chr(val)
        return result

    def _string2bool(self, s):
        lcase = s.lower()
        if lcase == "true" \
           or lcase == "yes" \
           or lcase == "1":
            return 1
        elif lcase == "false" \
             or lcase == "no" \
             or lcase == "0":
            return 0
        else:
            raise ValueError()
            

class Folder(NamespaceObject):
    """A folder. Does not contain the name of the folder itself."""
    def __init__(self, source, write_target, prefix):
        self.folders = {}
        self.parameters = {}
        # When adding new objects, we need to write them to some file.
        # We only need one write target. However, it may not be very easy
        # to figure out which write target to use. Example: This folder is defined
        # by a read-only machine-wide file, and also by a writable user-file. There are two
        # cases:
        #
        # 1) Mandatory settings, the machine-wide file is read first
        # In this case, the first read file is not writable, so we should choose
        # the second one. 
        #
        # 2) Default settings, the user file is read first.
        # The first file (the user file) is writable. Chose it. 
        #
        # So, we need to test if the source files are writable.

        # List of URLs that has contributed to this Folder.
        self.sources = []
        # URL to write to when adding new folder objects. 
        self.write_target = write_target
        # Mount prefix for this folder, in write_target. 
        self.prefix = prefix
        self._update(source)

    def _update(self, source):
        if source:
            self.sources.append(source)

    def _addobject(self, obj, objname):
        if self._exists(objname):
            raise ObjectExistsError

        if isinstance(obj, Parameter):
            print >>debugw, "Adding parameter", objname
            self.parameters[objname] = obj
        elif isinstance(obj, Folder):
            print >>debugw, "Adding folder", objname
            self.folders[objname] = obj
        else:
            raise InvalidObjectError

##     def create_new_folder(self, folderpath):
##         comps = path2comps(folderpath)
##         fold = _create_folders(self, comps, None)
##         # Write to disk
##         nice_folderpath = string.join(comps, "/")
##         sectionstring = "[%s]" % nice_folderpath

##         (scheme, netloc, filename, query, fragment) = urlparse.urlsplit(fold.write_target)
##         if not scheme == "file":
##             # Only able to write to local files right now
##             raise ReadOnlySource()

##         print >> open(filename, "a"), sectionstring

    def _get_object(self, objname):
        return self.folders.get(objname) or self.parameters.get(objname)
        
    def _exists(self, objname):
        return self.folders.has_key(objname) or self.parameters.has_key(objname)

    #
    # Get methods
    #

    def get_string(self, objpath):
        return self.lookup(objpath).get_string()

    # FIXME: The rest

    #
    # Set methods
    #
    
    # FIXME
    def set_string(self, parampath, new_value):
        comps = path2comps(parampath)
        folder = self._lookup_list(comps[:-1]) # FIXME: autocreate
        paramname = comps[-1]
        param = folder.lookup(paramname)
        if not param:
            # Add new parameter
            # Write new params to the file specified by the Folders
            # write_target
            source = folder.write_target

            # Sectionname
            prefix_comps = path2comps(folder.prefix)
            parampath_comps = comps[:-1]

            if not prefix_comps == parampath_comps[:len(prefix_comps)]:
                # folder prexis is not a prefix for parampath.
                # Something is wrong!
                raise "Internal error"

            sectionname = comps2path(parampath_comps[len(prefix_comps):])

            folder._addobject(Parameter(new_value, source,
                                        sectionname, paramname), paramname)
            # Write new parameter to disk
            # This should be done by parsing the folders write_target file
            # and fins the correct section, and then add this parameter just
            # below the section line.
            # FIXME
            
        else:
            # Update existing parameter
            param.set_string(new_value)

    def lookup(self, objpath):
        """Lookup an object. objname is like global/settings/background
        Returns None if object is not found."""
        comps = path2comps(objpath)
        return self._lookup_list(comps)

    def _lookup_list(self, comps):
        """Lookup an object. comps is like
        ["global", "settings", "background"]
        Returns None if object is not found. 
        """
        print >>debugw, "_lookup_list with components:", repr(comps)
        
        first_comp = comps[0]
        rest_comps = comps[1:] 
        
        obj = self._get_object(first_comp)
        if not obj:
            return

        if len(comps) == 1:
            # Last step in recursion
            return obj
        else:
            # Recursive call with rest of component list
            if not isinstance(obj, Folder):
                raise ObjectExistsError
            
            return obj._lookup_list(rest_comps)

    def walk(self, indent=None):
        if not indent:
            indent = IndentPrinter()

        # Print Parameters and values
        for (paramname, param) in self.parameters.items():
            print >> indent, paramname, "=", param.get_string(), " (sectionname:%s)" % param.sectionname

        # Print Foldernames and their contents
        for (foldername, folder) in self.folders.items():
            print >>indent, foldername + "/ (sources:%s, write_target:%s, prefix:%s)" % (folder.sources, folder.write_target, folder.prefix)
            indent.change(4)
            folder.walk(indent)
            indent.change(-4)


def open_hive(url):
    hfp = HiveFileParser(url)
    return hfp.parse()


class HiveFileParser:
    def __init__(self, url):
        # URL to entry hive
        self.url = url

    def parse(self, url=None, rootfolder=None, prefix="/"):
        """Open and parse a hive file. Returns a folder"""
        if not url:
            url = self.url
        
        url = fixup_url(url)
        file = urllib2.urlopen(url)

        if not rootfolder:
            rootfolder = Folder(url, url, prefix)
        curfolder = rootfolder
        linenum = 0
        sectionname = ""

        # Read & parse entire hive file
        while 1:
            line = file.readline()
            linenum += 1

            if not line:
                break

            line = line.strip()

            if line.startswith("#") or line.startswith(";") or not line:
                continue

            if line.startswith("["):
                # Folder
                if not line.endswith("]"):
                    raise SyntaxError

                sectionname = line[1:-1]
                print >>debugw, "Read section line", sectionname
                curfolder = self.handle_section(rootfolder, sectionname, url, prefix)

            elif line.startswith("%"):
                # Directive
                fields = line.split()
                directive = fields[0]
                args = fields[1:]

                # %mount
                if directive == "%mount":
                    self.mount_directive(args, curfolder, url, linenum, prefix, sectionname)
                else:
                    print >> sys.stderr, "%s: line %d: unknown directive" % (url, linenum)

            elif line.find("=") != -1:
                # Parameter
                (paramname, paramvalue) = line.split("=", 1)
                paramname = paramname.strip()
                paramvalue = paramvalue.strip()
                print >>debugw, "Read parameter line", paramname
                curfolder._addobject(Parameter(paramvalue, url, sectionname, paramname), paramname)
            else:
                raise SyntaxError(linenum)

        return rootfolder


    def handle_section(self, rootfolder, sectionname, source, prefix):
        print >>debugw, "handle_section for section", sectionname
        comps = path2comps(sectionname)

        folder = rootfolder._lookup_list(comps)
        if folder:
            # Folder already exists. Update with new information. 
            folder._update(source)
        else:
            folder = self._create_folders(rootfolder, comps, source, prefix)

        return folder


    # Create folder in memory. Not for external use.
    # The external function should also write folder to disk. 
    def _create_folders(self, folder, comps, source, prefix):
        first_comp = comps[0]
        rest_comps = comps[1:] 

        obj = folder._get_object(first_comp)
        if not obj:
            # Create folder
            if len(comps) == 1:
                # last step
                if not source:
                    # If no source, inherit
                    write_target = folder.write_target
                else:
                    write_target = source

                obj = Folder(source, write_target, prefix)
            else:
                obj = Folder(None, folder.write_target, prefix)

            folder._addobject(obj, first_comp)

        if len(comps) == 1:
            # Last step in recursion
            return obj
        else:
            # Recursive call with rest of component list
            if not isinstance(obj, Folder):
                raise ObjectExistsError

            return self._create_folders(obj, rest_comps, source, prefix)


    def mount_directive(self, args, curfolder, url, linenum, prefix, sectionname):
        try:
            opts, args = getopt.getopt(args, "t:a:")
        except getopt.GetoptError:
            print >> sys.stderr, "%s: line %d: invalid syntax" % (url, linenum)
            return

        format = "hive"
        format_args = ""
        for o, a in opts:
            if o == "-t":
                format = a
            if o == "-a":
                format_args = a

        if not len(args) == 1:
            print >> sys.stderr, "%s: line %d: invalid syntax" % (url, linenum)
            return

        # FIXME: Only glob for file URLs. 
        for mount_url in glob.glob(args[0]):
            if format == "hive":
                self.parse(mount_url, curfolder, os.path.join(prefix, sectionname))

            elif format == "parameter": # FIXME: Separate function/module/library
                paramname = "default" # FIXME

                # Parse parameter specific options
                for format_arg in format_args.split(","):
                    (name, value) = format_arg.split("=")
                    if name == "name":
                        paramname = value

                paramvalue = open(mount_url).read()
                curfolder._addobject(Parameter(paramvalue, mount_url, "", paramname), paramname)

            else:
                print >> sys.stderr, "%s: line %d: unsupported format" % (url, linenum)
                continue
        

class HiveFileUpdater:
    # FIXME: Broken for parameter files. 
    def __init__(self, source):
        self.source = source

        (scheme, netloc, self.filename, query, fragment) = urlparse.urlsplit(self.source)
        if not scheme == "file":
            # Only able to write to local files right now
            raise ReadOnlySource()

    def change_parameter(self, sectionname, paramname, new_value):
        """Change existing parameter line in file"""
        # FIXME: Use file locking
        f = open(self.filename, "r+")

        correct_section = 0 
        rest_data = ""
        parameter_offset = None

        # If this parameter is at top level, we are already in the
        # correct section when we start parsing. 
        if sectionname == "":
            correct_section = 1

        while 1:
            line_offset = f.tell()
            line = f.readline()

            if not line:
                break

            line = line.strip()
            
            if line.startswith("#") or line.startswith(";") or not line:
                continue

            if line.startswith("["):
                # Section
                if not line.endswith("]"):
                    # Ignore invalid section lines
                    continue

                correct_section = (sectionname == line[1:-1])
                
            elif correct_section and line.find("=") != -1:
                (line_paramname, line_paramvalue) = line.split("=", 1)
                line_paramname = line_paramname.strip()
                if paramname == line_paramname:
                    parameter_offset = line_offset
                    rest_data = f.read()
                    break

        if parameter_offset == None:
            # The parameter was not found!
            raise NoSuchParameterError()

        # Seek to parameter offset, and write new value
        f.seek(parameter_offset)
        print >> f, paramname + "=" + new_value

        # Write rest
        f.write(rest_data)
        f.truncate()

        
