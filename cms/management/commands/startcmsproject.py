#!/usr/bin/env python
import os
import subprocess
import sys

from django.core.checks.security.base import SECRET_KEY_INSECURE_PREFIX
from django.core.management import CommandError
from django.core.management.templates import TemplateCommand
from django.core.management.utils import get_random_secret_key

from cms import __version__ as cms_version

# There can be multiple commands like startcmsproject, updatecmsproject, deletecmsproject
# for implementing these commands we inherit from BaseCommand class
# here we are creating a template using our command hence we are inheriting from
# TemplateCommand class which in turn inherits from a generic BaseCommand class.
# If we want to implement a custom project template we can either modify this file
# or create a new command that inherits from a TemplateCommand, like maybe
# we want to create a command that adds an app to our existing project.
class Command(TemplateCommand):
    help = (
        "Creates a django CMS project directory structure for the given project "
        "name in the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide a project name."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # (Pdb) self.__dict__
        # {'stdout': <django.core.management.base.OutputWrapper object at 0x000001FE7D543080>,
        #  'stderr': <django.core.management.base.OutputWrapper object at 0x000001FE7D51D3D0>,
        #  'style': <django.core.management.color.Style object at 0x000001FE7D51D400>}

        # Version major.minor
        self.major_minor = ".".join(cms_version.split(".")[:2])

        # Both lines are defining formatting helpers for printing nicely-colored CLI output.
        # They rely on self.style, which comes from BaseCommand’s initializer:
        # self.style = color_style(force_color)
        # and color_style() creates an instance of Django’s Style class.
        # That class builds its color functions from the palettes in termcolors.py.

        # def color_style(force_color=False):
        # """
        # Return a Style object from the Django color scheme.
        # """
        #   if not force_color and not supports_color():
        #        return no_style()
        #   return make_style(os.environ.get("DJANGO_COLORS", ""))
        # Configure formatting
        # self.style is an instance of the Django Style class (created by color_style()),
        # which has attributes like .SQL_FIELD, .ERROR, .SUCCESS, etc.
        # self.style.SQL_FIELD is a function that colors text — specifically, 
        # in the default (“dark”) palette it’s:
        # SQL_FIELD → {"fg": "green", "opts": ("bold",)}
        # So calling it like:
        # self.style.SQL_FIELD("Run migrations")
        # returns:
        # "\x1b[1;32mRun migrations\x1b[0m"   # Bold green text in ANSI
        # The lambda adds a line break before that colored text:
        # lambda text: "\n" + self.style.SQL_FIELD(text)
        # 🧠 Effectively:
        # When the code later does:
        # self.stdout.write(self.HEADING("Run migrations"))
        # …it prints:
        # <newline>
        # [bold green]Run migrations[/reset]
        # So it visually separates sections in the CLI output —
        #  making headings stand out clearly.
        self.HEADING = lambda text: "\n" + self.style.SQL_FIELD(text)
        self.COMMAND = self.style.HTTP_SUCCESS
        # 1. djangocms myproject
        # (Pdb) self.major_minor
        # '5.1'
        # (Pdb) self.HEADING
        # <function Command.__init__.<locals>.<lambda> at 0x000001FE7D88E2A0>
        # (Pdb) self.COMMAND
        # <function make_style.<locals>.style_func at 0x000001FE7D85D800>

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells django CMS to NOT prompt the user for input of any kind. "
                "Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
            ),
        )
        parser.add_argument(
            "--username",
            help="Specifies the login for the superuser to be created",
        )
        parser.add_argument("--email", help="Specifies the email for the superuser to be created")

    def get_default_template(self):
        return f"https://github.com/django-cms/cms-template/archive/{self.major_minor}.tar.gz"

    def postprocess(self, project, options):
        # Go to project dir
        self.write_command(f'cd "{project}"')
        os.chdir(project)

        # Install requirements
        self.install_requirements(project)

        # Create database by running migrations
        self.stdout.write(self.HEADING("Run migrations"))
        self.run_management_command(["migrate"], capture_output=True)

        # Create superuser (respecting command line arguments)
        self.stdout.write(self.HEADING("Create superuser"))
        command = ["createsuperuser"]
        if options.get("username"):
            command.append("--username")
            command.append(options.get("username"))
        if options.get("email"):
            command.append("--email")
            command.append(options.get("email"))
        if not options["interactive"]:
            if "--username" not in command:
                command.append("--username")
                command.append(os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"))
            if "--email" not in command:
                command.append("--email")
                command.append(os.environ.get("DJANGO_SUPERUSER_EMAIL", "none@nowhere.com"))
            command.append("--noinput")
        self.run_management_command(command)

        # Check installation
        self.stdout.write(self.HEADING("Check installation"))
        self.run_management_command(["cms", "check"], capture_output=True)

        # Display success message
        message = f"django CMS {cms_version} installed successfully"
        separator = "*" * len(message)
        self.stdout.write(self.HEADING(f"{separator}\n{message}\n{separator}"))
        self.stdout.write(
            f"""
Congratulations! You have successfully installed django CMS,
the lean enterprise content management powered by Django!

Now, to start the development server first go to your newly
created project and then call the runserver management command:
$ {self.style.SUCCESS("cd " + project)}
$ {self.style.SUCCESS("python -m manage runserver")}

Learn more at https://docs.django-cms.org/
Join the django CMS Discord Server at https://discord-main-channel.django-cms.org

Enjoy!
"""
        )

    def install_requirements(self, project):
        for req_file in ("requirements.txt", "requirements.in"):
            requirements = os.path.join(project, req_file)
            if os.path.isfile(requirements):
                if self.running_in_venv() or os.environ.get("DJANGOCMS_ALLOW_PIP_INSTALL", "False") == "True":
                    self.stdout.write(self.HEADING(f"Install requirements in {requirements}"))
                    self.write_command(f'python -m pip install -r "{requirements}"')
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements],
                        capture_output=True, check=False,
                    )
                    if result.returncode:
                        self.stderr.write(self.style.ERROR(result.stderr.decode()))
                        raise CommandError(f"Failed to install requirements in {requirements}")
                    break
                else:
                    self.stderr.write(
                        self.style.ERROR(
                            "To automatically install requirements for your new django CMS "
                            "project use this command in an virtual environment."
                        )
                    )
                    raise CommandError("Requirements not installed")

    def run_management_command(self, commands, capture_output=False):
        self.write_command("python -m manage " + " ".join(commands))
        result = subprocess.run([sys.executable, "-m", "manage"] + commands, capture_output=capture_output, check=False)
        if result.returncode:
            if capture_output:
                self.stderr.write(self.style.ERROR(result.stderr.decode()))
            raise CommandError(f"{sys.executable} -m manage {' '.join(commands)} failed.")

    def write_command(self, command):
        self.stderr.write(self.COMMAND(command))

    @staticmethod
    def running_in_venv():
        return sys.prefix != sys.base_prefix

    def handle_template(self, template, subdir):
        if not template:
            template = self.get_default_template()
        return super().handle_template(template, subdir)

    def handle(self, **options):
        # Capture target and name for postprocessing
        name = options.pop("name")
        directory = options.pop("directory", None)
        # Create a random SECRET_KEY to put it in the main settings.
        options["secret_key"] = SECRET_KEY_INSECURE_PREFIX + get_random_secret_key()

        self.stdout.write(self.HEADING("Clone template using django-admin"))
        command = (
            f'django-admin startproject "{name}" ' f'--template {options["template"] or self.get_default_template()}'
        )
        if directory:
            command += f' --directory "{directory}"'
        self.write_command(command)

        # Run startproject command
        super().handle(
            "project", name, directory, cms_version=cms_version, cms_docs_version=self.major_minor, **options
        )

        if directory is None:
            top_dir = os.path.join(os.getcwd(), name)
        else:
            top_dir = os.path.abspath(os.path.expanduser(directory))
        self.postprocess(top_dir, options)
