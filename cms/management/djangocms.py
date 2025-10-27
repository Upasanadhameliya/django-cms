import os
import sys

from django.core.management import load_command_class


def execute_from_command_line(argv=None):
    """Run the startcmsproject management command."""

    # 1. djangocms myproject
    # (Pdb) sys.argv
    # ['C:\\Sandy\\Documents\\OpenSource\\DjangoCMS\\main-repo\\.venv\\Scripts\\djangocms', 
    # 'trial1']

    # Prepare arguments
    # sys.arv[:] creates a shallow copy so that we don't modify the original copy
    # -> Why a shallow copy is enough here?
    # The contents of sys.argv look something like this:
    # ['djangocms', 'myproject', '--verbose']
    # That’s a flat list of strings — there are no nested lists, dicts, or mutable objects.
    # Now, strings in Python are immutable — you can’t modify them in place.
    # So even if you copied the list shallowly:
    # argv = sys.argv[:]
    # and then changed one element:
    # argv[0] = "python"
    # you’re reassigning a list slot, not mutating the string "djangocms" itself.
    # Thus, modifying argv doesn’t affect sys.argv.
    argv = argv or sys.argv[:]
    
    # 1. djangocms myproject
    # (Pdb) argv
    # ['C:\\Sandy\\Documents\\OpenSource\\DjangoCMS\\main-repo\\.venv\\Scripts\\djangocms', 'trial-project']
    
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

    # 1. djangocms myproject
    # (Pdb) argv
    # ['djangocms', 'trial-project']

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
    # execute_from_command_line()" (makes a new inline script here.)

    # When you run a one-liner with python -c "...", 
    # Python treats that string as a script. Internally:
    # __name__ = "__main__"
    # This is true for any Python code executed via -c, 
    # because Python is essentially running it as a script — 
    # it didn’t import it as a module.
    
    # So case 3 for djangocms <project-name> because djangocms.exe is running a new script
    # which imports execute_from_command_line from cms.management.djangocms.
    if argv[0] == "__main__.py":
        # if we run it as python -m cms.management.djangocms myproject
        # i.e. Case 2, thenargv[0] is __main__.py and then our argv would be
        # ["python -m cms", "myproject"]
        argv[0] = "python -m cms"

    # 1. djangocms myproject
    # (Pdb) argv
    # ['djangocms', 'trial-project']

    # Find command
    # The function load_command_class(app_name, name) is Django’s internal 
    # way of locating and importing a management command from a given app.
    # It searches for a command file with this pattern:
    # <app_name>/management/commands/<name>.py
    # and returns the Command class defined inside that file.
    # So in this case:
    # load_command_class("cms", "startcmsproject")
    # Django will try to import:
    # cms.management.commands.startcmsproject
    # and then grab its Command class.
    # The first argument ("cms") tells Django which app the management command belongs to.
    # In other words, it tells Django to look for the command inside the module:
    # cms.management.commands.startcmsproject
    # load_command_class() returns an instance of the Command class — not the class itself.
    # So after that line, *command is an object*, not a class definition.
    # Also currently "djangocms" maps to the internal command "startproject", but then
    # later we may decide to map it to a command called "updateproject" or we might
    # want to change the name of "djangocms" to "djcms" or "cms-admin" in that case
    # the decoupling of "startcmsproject" (which is an internal command) and "djangcms"
    # (which is an external command) is useful. We might also want to map the same two
    # arguments "django-cms" and "djangocms" to "startcmsproject" or map the same one
    # argument "djangocms" to different internal commands like "startcmsproject" and 
    # "updatecmsproject" based on a flag or the number of arguments like djangocms mp1
    # should mean startcmsproject but djangocms mp1 mp2 should mean updatecmsproject
    # from mp1 to mp2 something like that.
    command = load_command_class("cms", "startcmsproject")
    
    # 1. djangocms myproject
    # (Pdb) command
    # <cms.management.commands.startcmsproject.Command object at 0x0000016EA7C7DB80>

    if argv[1:] == ["--version"]:
        from cms import __version__
        sys.stdout.write(__version__ + "\n")
    elif argv[1:] == ["--help"]:
        command.print_help(argv[0], "")
    else:
        command.run_from_argv([argv[0], ""] + argv[1:])  # fake "empty" subcommand
