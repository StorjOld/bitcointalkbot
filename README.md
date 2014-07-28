bitcointalkbot
==============

For monitoring keywords on Bitcointalk, and posting them to Slack.

How to run:

    $ virtualenv -p $path-to-python-3.4-binary> venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    # edit crawler.py config
    $ python crawler.py