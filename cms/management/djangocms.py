import os
import sys

from django.core.management import load_command_class


def execute_from_command_line(argv=None):
    """Run the startcmsproject management command."""

    # Prepare arguments
    # sys.arv[:] creates a shallow copy so that we don't modify the original copy
    argv = argv or sys.argv[:]
    
    # This line makes sure it’s a clean filename — not a long path.
    # Let’s say the OS invoked your program as:
    # /Users/sandy/.local/bin/djangocms myproject
    # Then sys.argv would be:
    # ['/Users/sandy/.local/bin/djangocms', 'myproject']
    # After this line runs:
    # argv[0] = os.path.basename(argv[0])
    # Now argv[0] = 'djangocms'
    # So the command name shown in help messages and 
    # error traces becomes shorter and cleaner.
    argv[0] = os.path.basename(argv[0])

    # Case - When running it as:
    # python -m cms.management.djangocms myproject
    # When Python sees -m modulename, it doesn’t execute python modulename.py — 
    # it imports that module as a script using the internal runpy mechanism:
    # import runpy
    # runpy.run_module('cms.management.djangocms', run_name='__main__')
    # Now, inside the running code of cms.management.djangocms.py:
    # __name__ == "__main__" ✅
    # But sys.argv is not modified by runpy (except for argv[0])!
    # So Python replaces sys.argv[0] (cms.management.djangocms) 
    # with a fake name like "__main__.py".
    # That’s how the file “knows” it’s being executed as a module via -m.

    # 🟢 Case 1: run the file directly
    # python cms/management/djangocms.py myproject
    # Output:
    # __name__ = __main__
    # sys.argv = ['cms/management/djangocms.py', 'myproject']

    # 🟢 Case 2: run it as a module
    # python -m cms.management.djangocms myproject
    # Output:
    # __name__ = __main__
    # sys.argv = ['__main__.py', 'myproject']

    # 🟢 Case 3: Run via entry point (djangocms.exe)
    # djangocms myproject
    # Output:
    # __name__ = cms.management.djangocms
    # sys.argv = ['djangocms', 'myproject']

    # What actually happens when you type djangocms myproject
    # djangocms.exe is a small stub executable created by pip (via setuptools).
    # Its job is to launch Python with the right module and function.
    # On Windows, that stub runs something like this internally:
    # python.exe -c 
    # "from cms.management.djangocms import execute_from_command_line; 
    # execute_from_command_line()"
    
    # So case 3 for djangocms <project-name> because djangocms.exe is running a new script
    # which imports execute_from_command_line from cms.management.djangocms.
    if argv[0] == "__main__.py":
        argv[0] = "python -m cms"

    # Find command
    command = load_command_class("cms", "startcmsproject")
    if argv[1:] == ["--version"]:
        from cms import __version__
        sys.stdout.write(__version__ + "\n")
    elif argv[1:] == ["--help"]:
        command.print_help(argv[0], "")
    else:
        command.run_from_argv([argv[0], ""] + argv[1:])  # fake "empty" subcommand
