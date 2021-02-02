from flask import Flask, render_template, request, send_file, session, redirect, url_for
from process_result import get_users_results
import csv
import time
import datetime
import traceback
import os
from rq import Queue
from rq.job import Job
from redis import Redis
from worker import conn

app = Flask(__name__)
q = Queue(connection=conn)
local=False

if local:
    app.config.from_pyfile('instance/config.py')
else:
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/form_result", methods=["GET", "POST"])
def form_result():
    if request.method == "POST":
        try:
            userdata = dict(request.form)
            username = userdata["username"]
            password = userdata["password"]
            year = userdata["year"]
            session["username"] = username
            session["password"] = password 
            session["year"] = year
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
            filename = 'data/' + username + '_' + year + '_history_' + st + '.csv'
            session["filename"] = filename
            job = q.enqueue(get_users_results, username, password, int(year), filename, job_timeout=1800) # 30 min timeout
            print(f"Status: submitted job for user {username} (job id {job.id})")
            print(f"Status: queue status ({len(q)} waiting, {q.finished_job_registry.count} finished, {q.failed_job_registry.count} failed)")
            return redirect(url_for('result', id=job.id))
        except:
            traceback.print_exc()
            return render_template("error.html")
    else:
        return render_template("error.html")

@app.route('/result/<string:id>')
def result(id):
    job = Job.fetch(id, connection=conn)
    status = job.get_status()
    if status in ['queued', 'started', 'deferred']:
        return render_template("refresh.html", result=status, refresh=True)
    elif status == 'failed':
        print(f"Status: job {id} failed")
        # check for timeout
        if 'JobTimeoutException' in job.__dict__["exc_info"].split("raise")[-1]:
            return render_template("timeouterror.html")
        return render_template("error.html")
    elif status == 'finished':
        result = job.result
        if not result: # login error
            return render_template('loginerror.html')
        csv_output, stats, num_works = result
        print(f"Status: job {id} succeeded ({num_works} works)")
        if not os.path.exists('data'):
            os.makedirs('data')
        filename = session.get("filename")
        header, rows = csv_output
        if len(rows) == 0:
            return render_template('no_results.html', year=stats['year'])
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
        items=[{"name":'name_str', "val":'1'}]
        return render_template('results.html', data=stats, items=items)

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")

@app.route("/technical")
def technical():
    return render_template("technical.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
  
@app.route("/download")
def download():
    filename = session.get("filename")
    return send_file(filename, as_attachment=True)      
      
if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
