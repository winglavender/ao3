from flask import Flask, render_template, request, send_file, session, redirect, url_for, render_template_string
from process_result import get_users_results
import csv
import time
import datetime
import sys
import traceback
import os
from rq import Queue
from rq.job import Job
from redis import Redis
from worker import conn

app = Flask(__name__)
q = Queue(connection=conn)
local=True

if local:
    app.config.from_pyfile('instance/config.py')
else:
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))

template_str='''<html>
    <head>
      {% if refresh %}
      <meta http-equiv="refresh" content="5">
      {% endif %}
    </head>
    <body>{{result}}</body>
    </html>'''

def get_template(data, refresh=False):
    return render_template('results.html', data=data, refresh=refresh)
    #return render_template_string(template_str, result=data, refresh=refresh)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/form_result", methods=["GET", "POST"])
def form_result():
    if request.method == "POST":
        try:
            #start_time = time.time()
            userdata = dict(request.form)
            if local:
                username = userdata["username"]
                cookie = userdata["cookie"]
                year = userdata["year"]
            else:
                username = userdata["username"]
                cookie = userdata["cookie"]
                year = userdata["year"]
            session["username"] = username
            session["cookie"] = cookie
            session["year"] = year
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
            if not os.path.exists('data'):
                os.makedirs('data')
            filename = 'data/' + username + '_' + year + '_history_' + st + '.csv'
            session["filename"] = filename

            # new 
            job = q.enqueue(get_users_results, username, cookie, int(year), filename)
            #data = username
            #job = q.enqueue(slow_func, data)
            return redirect(url_for('result', id=job.id))

            # old
            #results = process_result.get_users_results(username, cookie, int(year))
            #if not results:
            #    return render_template("loginerror.html")
            #csv_output, stats = results
            #header, rows = csv_output
            #with open(filename, 'w', newline='') as csvfile:
            #    writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            #    writer.writerow(header)
            #    for row in rows:
            #        writer.writerow(row)
            #print("--- Runtime: %s minutes ---" % ((time.time() - start_time)/60))
            #stats["year"] = year
            #return render_template("results.html", data=stats)
        except:
            traceback.print_exc()
            return render_template("error.html")
    else:
        return render_template("error.html")

@app.route('/result/<string:id>')
def result(id):
    job = Job.fetch(id, connection=conn)
    status = job.get_status()
    if status in ['queued', 'started', 'deferred', 'failed']:
        return render_template_string(template_str, result=status, refresh=True)
        #return get_template(status, refresh=True)
    elif status == 'finished':
        result = job.result
        return render_template('results.html', data=result)
        #return get_template(result)

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")
  
@app.route("/download")
def download():
    filename = session.get("filename")
    print(filename)
    return send_file(filename, as_attachment=True)      
      
if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
