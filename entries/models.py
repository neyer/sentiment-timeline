from __future__ import unicode_literals

from django.db import models
from HTMLParser import HTMLParser
from datetime  import datetime, timedelta
from dateutil import parser
import itertools
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import word_tokenize
import mailbox
import json

logging.basicConfig()
logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()
unescape = HTMLParser().unescape

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def clean_html_text(in_text):
  unescaped = unescape(in_text)
  s = MLStripper()
  s.feed(unescaped)
  return s.get_data()

# Create your models here.

class Entry(models.Model):
  Source_Hangouts = 0
  Source_GMail = 1

  timestamp = models.FloatField()
  source = models.IntegerField()
  text = models.TextField()


  @property 
  def human_time(self):
    return datetime(1970,1,1) + timedelta(seconds=self.timestamp)

  @property
  def normalized_text(self):
    return clean_html_text(self.text.strip())

  def get_scores(self):
   return analyzer.polarity_scores(self.normalized_text)

  def get_weighted_scores(self):
    word_len = len(self.text.split(' '))

    scores = self.get_scores()
    return { k : scores[k]*word_len for  k in scores}

  @property
  def negative_score(self):
    scores = self.get_scores()
    return scores['neg']


  @classmethod
  def build_all_from_mbox_file(class_, mbox_file_name, self_email):

    logger.info("Loading messages from {} in {} ".format(self_email, mbox_file_name))
    logger.info("This can take a while (10-30 minutes)")
    # for processing messages from mbox file
    def get_message_timestamp(item):
       from_s = item.get_from()
       parts = from_s.split()
       timestamp = ' '.join(parts[1:])
       dt = parser.parse(timestamp)
       dt = dt.replace(tzinfo=None)
       return (dt-datetime(1970,1,1)).total_seconds()

    def is_from_me(item):
      values = item.values()
      from_addr = item['From'] or []
      labels = item['X-Gmail-Labels'] or []
      return (self_email in from_addr) and ('Chat' in labels)


    mail = mailbox.mbox(mbox_file_name)
    # store this on the class
    num_made = 0
    class_.last_mailbox = mail
    for item in mail:
      if is_from_me(item):
        ts = get_message_timestamp(item)
        body = item.get_payload()
        try:
          class_.objects.create(
              timestamp=ts,
              text=body,
              source=Entry.Source_GMail
          )
          num_made += 1

          if num_made % 1000 == 0:
            logger.info('Created {} entries.'.format(num_made))
        except: pass

  def get_bigrams(self):
    tokens = word_tokenize(self.normalized_text)
    a,b = itertools.tee(tokens, 2)

    next(b, None)
    return list(itertools.izip(a,b))

  def get_trigrams(self):
    tokens = word_tokenize(self.normalized_text)
    a,b,c = itertools.tee(tokens, 3)

    next(b, None)
    next(c, None)
    next(c, None)
    return list(itertools.izip(a,b,c))

  @classmethod
  def generate_trigram_table(class_, entries):
    trigrams = {}

    total_count = 0
    for entry in entries:
      these_trigrams = entry.get_trigrams()
      for trigram in these_trigrams:
        total_count += 1
        trigram = ' '.join(trigram)
        trigrams[trigram] = trigrams.setdefault(trigram, 0) + 1


    sorted_parts = sorted([(k,v) for k,v in trigrams.items()],
        key=lambda entry :-entry[1])

    return [ (words, count/float(total_count)) for words,count in sorted_parts ]

  @classmethod
  def compute_frequency_table_delta(class_, freq_table_1, freq_table_2):
    """Given two frequency tables, compute the delta between the two"""
    dict_1 = dict(freq_table_1)
    dict_2 = dict(freq_table_2)

    output = {}

    for phrase, count_in_1 in dict_1.iteritems():
      count_in_2 = dict_2.get(phrase) or 0
      output[phrase] = count_in_2 - count_in_1
    for phrase, count_in_2 in dict_2.iteritems():
      if not phrase in dict_1:
        output[phrase] = count_in_2
    return sorted([(k,v) for k,v in output.items()],
          key=lambda entry:entry[1])

  @classmethod
  def generate_data_series(class_):

    series_names = ['pos', 'neg', 'neu']

    points_by_week = {}
    max_distance = 60*60*24*7
    result = []
    this_batch_values = []
    this_batch_time = None

    for e in Entry.objects.order_by('timestamp'):
      if not this_batch_time:
        this_batch_time = e.timestamp
        this_batch_values = [ e ]
      elif e.timestamp - this_batch_time > max_distance:
        # end this batch
        points_by_week[this_batch_time] =  { 
            'entries': this_batch_values,
            'count': len(this_batch_values)
        }
        this_batch_values = []
        this_batch_time = None
      else:
        this_batch_values.append(e)

    # now compute the metrics for each week

    for week_key, data in points_by_week.items():
      scores_this_week = { n:0 for n in series_names}
      counts_this_week = { n:0 for n in series_names}

      total_points = data['count']
      for entry in data['entries']:
        scores = entry.get_scores()
        for name in series_names:
          value = scores[name]
          scores_this_week[name] += value
          if value:
            counts_this_week[name] += 1

      data['sum_scores'] = scores_this_week

      for name in series_names:
        name_count = counts_this_week[name]
        if name == 'neg':
          name_count = -name_count
        if name_count:
          average = scores_this_week[name]/name_count
        else:
          average = 0
        data[name+'_average'] = average
        data[name+'_count']  = name_count/7.0
        frac = 0
        if total_points:
          frac = name_count/float(total_points)
        data[name+'_frac']  = frac

      data['delta_of_counts'] = data['pos_count'] + data['neg_count']

    serieses = {}


    week_ts = points_by_week.keys()
    week_ts.sort()

    to_extract = ['delta_of_counts']
    for name in series_names:
      to_extract = to_extract+ [name+'_average', name+'_count', name+'_frac',]
    for week_key in week_ts:
      data = points_by_week[week_key]
      for name in to_extract:
        serieses.setdefault(name,[]).append([week_key*1000, data[name]])

    return serieses

  @classmethod
  def write_series_to_file(class_, file_name):

    entry_count = Entry.objects.count()
    logger.info("Generating data series from {} entries".format(entry_count))
    series = class_.generate_data_series()

    with open(file_name, 'w') as f:
      f.write(json.dumps(series))
