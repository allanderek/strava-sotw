from bottle import route
import bottle
import jinja2
import requests

class Database(object):
    """ This is the interface to the database. Initially to get things started
        we do not need to actually create a persistant storage database because
        we only have one permanent group with an immutable set of athletes
    """
    def __init__(self):
        pass
    def get_group(self, group_id):
        if group_id == 1:
            return ['4634808', '2861283', '3919949', '1469231']
        else:
            raise KeyError
    def get_groups(self):
        return ['1']

database = Database()
application = bottle.default_app()

root_template_string = """
<!DOCTYPE>
<html>
<head>
  <title>Strava - Segment Of The Week</title>
</head>
<body>
<div class="container" style="display:table">
<div class="navigation" style="display:table-cell;
     vertical-align:top; padding-right:10px">
<ul>
  <li><a href="/">Welcome</a></li>
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


welcome_template_string = """
{% extends root_template %}
{% block content %}
<h1><b>S</b>egment <b>O</b>f <b>T</b>he <b>W</b>eek</h2>
<p>
A simple website to show a group of athletes competing over a particular segment.
To view times for a particular group over a particular segment create the url
of the form: <code>{{root_url}}times/&lt;group number&gt;/&lt;segment number&gt;</code>.
</p>
<p>
{% set example_url = root_url + 'times/1/8428538' %}
For example: <a href="{{example_url}}">{{example_url}}</a>
</p>
<h3>Groups</h3>
<ul>
    {% for group in group_ids %}
    <li> {{group}} </li>
    {% endfor %}
</ul>
</ol>
{% endblock %}
"""
welcome_template = jinja2.Template(welcome_template_string)


@route('/')
def welcome(message=None):
    """ Returns the welcome page."""
    group_ids = database.get_groups()
    template_dict = {'root_template': root_template,
                     'root_url': bottle.request.url,
                     'group_ids': group_ids}
    if message is not None:
        template_dict['message'] = message
    return welcome_template.render(**template_dict)


times_template_string = """
{% extends root_template %}
{% block content %}
A simple website to show a group of athletes competing over a particular segment.
<h1>Segment of the Week</h1>
<h2>{{segment_times.segment}} - best times</h2>
<ol>
{% for (athlete, time) in segment_times.times %}
    <li> {{athlete.first_name}} {{athlete.last_name}} - {{time}} </li>
{% endfor %}
</ol>
{% if segment_times.no_times %}
    <h2>{{segment_times.segment}} - No times</h2>
    These athletes have not yet set a time for this segment:
    <ul>
        {% for athlete in segment_times.no_times %}
            <li> {{athlete.first_name}} {{athlete.last_name}}</li>
        {% endfor %}
    </ul>
{% endif %}
{% endblock %}
"""
times_template = jinja2.Template(times_template_string)


@route('/times/<group_id:int>/<segment_id:int>')
def group_segment_times(group_id, segment_id):
    """ Returns the welcome page."""
    athlete_ids = database.get_group(group_id)
    athletes = [Athlete(id) for id in athlete_ids]
    segment_times = SegmentTimes(str(segment_id), athletes)
    try:
        segment_times.refresh_times()
    except InvalidSegment as exc:
        message = "Invalid segment number: " + str(exc.segment)
        return welcome(message=message)
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

class InvalidSegment(Exception):
    def __init__(self, segment):
        self.segment = segment

class Athlete(object):
    def __init__(self, athlete_id):
        self.id = athlete_id
        self.json = get_athlete_info(athlete_id)
        self.first_name = self.json['firstname']
        self.last_name = self.json['lastname']

    def get_segment_time(self, segment):
        url_template = 'https://www.strava.com/api/v3/segments/{0}/all_efforts'
        url = url_template.format(segment)
        parameters = {'athlete_id': self.id,
                      'access_token': access_token}
        response = requests.get(url, parameters)
        if response.status_code != 200:
            raise InvalidSegment(segment)
        json = response.json()
        times = [result['elapsed_time'] for result in json]
        return min(times) if times else "no time"

class SegmentTimes(object):
    def __init__(self, segment, athletes):
        self.segment = segment
        self.athletes = athletes
        self.times = []
        self.no_times = []

    def refresh_times(self):
        times = [(a, a.get_segment_time(self.segment)) for a in self.athletes]
        self.no_times = [a for (a, t) in times if t == 'no time']
        self.times = [(a, t) for (a, t) in times if t != 'no time']
        self.times.sort(key=lambda p: p[1])


import unittest
import webtest

class SimpleTest(unittest.TestCase):
    def test_welcome(self):
        test_app = webtest.TestApp(application)
        response = test_app.get('/')
        self.assertEqual(response.status, '200 OK')
        expected = '<b>S</b>egment <b>O</b>f <b>T</b>he <b>W</b>eek'
        self.assertIn(expected, response)

    def test_times(self):
        test_app = webtest.TestApp(application)
        response = test_app.get('/times/1/8428538')
        self.assertEqual(response.status, '200 OK')
        for (name) in ["Ross Houston", "Pat Gie",
                       "Jonathan Carpenter", "Christopher O'Brien"]:
            time_string_begin = "<li> {0} - ".format(name)
            self.assertIn(time_string_begin, response)

    def test_invalid_segment(self):
        test_app = webtest.TestApp(application)
        response = test_app.get('/times/1/22978393')
        self.assertEqual(response.status, '200 OK')
        expected = 'Message: Invalid segment number: 22978393'
        self.assertIn(expected, response)

if __name__ == "__main__":
    bottle.run(host='localhost', port=8080, debug=True)

