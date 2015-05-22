from bottle import route, default_app
import bottle
import jinja2
import requests

root_template_string = """
<!DOCTYPE>
<html>
<head>
  <title>{% block title %}{% endblock %} - Strava
  <b>S</b>egment <b>O</b>f <b>T</b>he <b>W</b>eek
  </title>
</head>
<body>
<div class="container" style="display:table">
<div class="navigation" style="display:table-cell;
     vertical-align:top; padding-right:10px">
<ul>
  <li><a href="/">Times</a></li>
</ul>
</div>
<div class="main-content" style="display:table-cell; vertical-align:top;">
  {% if message is defined %}
  <p><font color="red">Message: {{ message }}</font></p>
  {% endif %}
  <div id="content">{% block content %}{% endblock %}</div>
</div>
</div>
</body>
</html>
"""
root_template = jinja2.Template(root_template_string)


times_template_string = """
{% extends root_template %}
{% block title %}Segment of the Week - Times{% endblock %}
{% block content %}
A simple website to show a group of athletes competing over a particular segment.
<h1>Segment of the Week</h1>
<h2>{{segment_times.segment}}</h2>
<ol>
{% for (athlete, time) in segment_times.times.items() %}
    <li> {{athlete.first_name}} {{athlete.last_name}} - {{time}} </li>
{% endfor %}
</ol>


{% endblock %}
"""
times_template = jinja2.Template(times_template_string)


@route('/')
def welcome():
    """ Returns the welcome page."""
    athlete_ids = ['4634808', '2861283', '3919949', '1469231']
    athletes = [Athlete(id) for id in athlete_ids]
    segment_times = SegmentTimes('8428538', athletes)
    segment_times.refresh_times()
    return times_template.render(root_template=root_template,
                                 segment_times=segment_times)


access_token = '4c02177afff7fd3b1f35b66739d3c901daedf411'

def get_athlete_info(athlete_id):
    url_template = 'https://www.strava.com/api/v3/athletes/{0}'
    url = url_template.format(athlete_id)
    parameters = {'athlete_id': athlete_id,
                  'access_token': access_token}
    response = requests.get(url, parameters)
    json = response.json()
    return json

class Athlete(object):
    def __init__(self, athlete_id):
        self.id = athlete_id
        self.json = get_athlete_info(athlete_id)
        self.first_name = self.json['firstname']
        self.last_name = self.json['lastname']

def get_athlete_segment_time(athlete_id, segment):
    url_template = 'https://www.strava.com/api/v3/segments/{0}/all_efforts'
    url = url_template.format(segment)
    parameters = {'athlete_id': athlete_id,
                  'access_token': access_token}
    response = requests.get(url, parameters)
    json = response.json()
    times = [result['elapsed_time'] for result in json]
    return min(times)

class SegmentTimes(object):
    def __init__(self, segment, athletes):
        self.segment = segment
        self.athletes = athletes
        self.times = dict()

    def refresh_times(self):
        for athlete in self.athletes:
            self.times[athlete] = get_athlete_segment_time(athlete.id,
                                                           self.segment)

bottle.run(host='localhost', port=8080)

