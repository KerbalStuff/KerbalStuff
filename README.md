# KerbalStuff

Website for Kerbal Space Program mods.

http://www.kerbalstuff.com

## Installation

Quick overview:

1. Install Python 3, node.js, virtualenv, PostgreSQL
2. Set up aforementioned things
3. Clone KerbalStuff repository
4. Activate the virtualenv
5. Install pip requirements
6. Install coffeescript
7. Configure KerbalStuff
8. SQL
9. Site configuration

**Install the dependencies**

You'll need these things:

* Python 3
* Node.js
* virtualenv
* PostgreSQL

Use the packages your OS provides, or build them from source.

**Set up services**

Do a quick sanity check on all of those things.

    $ python3 --version
      Python 3.4.1
    $ node --version
      v0.10.29
    $ npm --version
      1.4.14
    $ pip --version
      pip 1.5.6 from /usr/lib/python3.4/site-packages (python 3.4)
    $ virtualenv --version
      1.11.6
    $ psql --version
      psql (PostgreSQL) 9.3.4

YMMV if you use versions that differ from these.

I'll leave you to set up PostgreSQL however you please. Prepare a connection
string that looks like this when you're done:

    postgresql://username:password@hostname:port/database

The connection string I use on localhost is this:

    postgresql://postgres@localhost/kerbalstuff

KerbalStuff needs to be able to create/alter/insert/update/delete in the database
you give it.

**Clone KerbalStuff**

Find a place you want the code to live.

    $ git clone git://github.com/SirCmpwn/KerbalStuff.git
    $ cd KerbalStuff

**Activate virtualenv**

    $ virtualenv --no-site-packages .
    $ source bin/activate

If you're like me and are on a system where `python3` is not the name of your
Python executable, use `--python=somethingelse` to fix that.

**pip requirements**

    $ pip install -r requirements.txt

**CoffeeScript**

    # npm install coffee-script
    $ coffee # Sanity check, press ^D to exit

**Configure KerbalStuff**

    $ cp alembic.ini.example alembic.ini
    $ cp config.ini.example config.ini

Edit config.ini and alembic.ini to your liking.

**Site Configuration**

What you do from here depends on your site-specific configuration. If you just
want to run the site for development, you can source the virtualenv and run

    python app.py

To run it in production, you probably want to use gunicorn behind an nginx proxy.
There's a sample nginx config in the configs/ directory here, but you'll probably
want to tweak it to suit your needs. Here's how you can run gunicorn, put this in
your init scripts:

    /path/to/KerbalStuff/bin/gunicorn app:app -b 127.0.0.1:8000

The `-b` parameter specifies an endpoint to use. You probably want to bind this to
localhost and proxy through from nginx. I'd also suggest blocking the port you
choose from external access. It's not that gunicorn is *bad*, it's just that nginx
is better.

When running in a production enviornment, run `python app.py` at least once and
then read the SQL stuff below before you let it go for good.

## SQL Stuff

We use alembic for schema migrations between versions. The first time you run the
application, the schema will be created. However, you need to tell alembic about
it. Run the application at least once, then:

    $ cd /path/to/KerbalStuff/
    $ source bin/activate
    $ python
    >>> from alembic.config import Config
    >>> from alembic import command
    >>> alembic_cfg = Config("alembic.ini")
    >>> command.stamp(alembic_cfg, "head")
    >>> exit()

Congrats, you've got a schema in place. Run `alembic upgrade head` after pulling
the code to update your schema to the latest version. Do this before you restart
the site.
