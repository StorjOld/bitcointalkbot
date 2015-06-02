bitcointalkbot
==============

For monitoring keywords on Bitcointalk, and posting them to Slack.

How to install and run on a clean install of Ubuntu 14.04 (LTS):

    sudo apt-get -y install python-virtualenv python-pip git
    virtualenv -p /usr/bin/python3.4 venv
    source venv/bin/activate
    git clone https://github.com/Storj/bitcointalkbot.git
    cd bitcointalkbot/
    pip install -r requirements.txt
    edit crawler.py # config
    python crawler.py
