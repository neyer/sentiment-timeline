# What it is:
This is a django application that allows you to generate a timeline showing how your mood has changed over time. 

It reads in an .mbox file ([which you can get from Google Takeout](https://support.google.com/accounts/answer/3024190?source=gsearch&hl=en)), and looks for outbound instant messages from the email addreses you give it. That allows it to build a store of Entries, which contain a timestamp, and some text you wrote at the time.

The program then uses [VADER sentiment analysis](http://www.nltk.org/_modules/nltk/sentiment/vader.html) to assign a 'mood score' to each piece of text.  This mood score is then used to generate a piece of JSON, which is fed to a web front end, rendering charts using [flot.js](https://github.com/flot/flot)

# How to use it:

* Get a python installation set up. I use a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/). 
* Run `pip install -r requirements.txt` to install all the python libraries
* Run `python manage.py migrate` to  create your database
* Run `python manage.py build_chart <your gmail address> <path to your data file>` . This will take a while.  The python library for parsing mbox files first builds a massive index, so you'll see very litle output at first, especially if your data file is huge.

* Run 'python manage.py runserver', and visit 127.0.0.1:8000


# Notes:

* It make ask you to download some data files for the nltk dataset. [This page has more info.](http://www.nltk.org/data.html)
*  To make it go faster, use a proper database instead of sqlite. The settings are in timeline/settings.py.$
* The web server is just hosting static files, it's not really needed. The 'template' in 'entries/templatesentries/index.html' is just a static file which makes a refernces to moods.json. I created this app as a django project so I could get the ORM, which I only kind of sort of used. 

* There is also some code inside to compute trigram frequency tables. You can also compute the delta of two trigram frequency tables. I used this to see how my language had changed over time. Feel free to poke around!



# License:
GPL

Sentiment-Timeline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sentiment-Timeline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
