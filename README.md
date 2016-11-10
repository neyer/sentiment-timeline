# how to use

* Get a python installation set up. I use a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/). 
* Run `pip install -r requirements.txt` to install all the python libraries
* Run `python manage.py migrate` to  create your database`
* Run `python manage.py build_chart <your gmail address ><path to your data file>` . This will take a while

* Run 'python manage.py runserver', and visit 127.0.0.1:8000


# Notes:

* It make ask you to download some data files for the nltk dataset. [This page has more info.](http://www.nltk.org/data.html)
*  To make it go faster, use a proper database instead of sqlite. The settings are in timeline/settings.py.$
* The web server is just hosting static files, it's not really needed.
