from flask import Flask, render_template, request, send_file, session
import process_result
import csv
import time
import datetime
import sys
import traceback

app = Flask(__name__)
app.config.from_pyfile('instance/config.py')


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/form_result", methods=["GET", "POST"])
def form_result():
    if request.method == "POST":
        try:
            start_time = time.time()
            userdata = dict(request.form)
            username = userdata["username"][0]
            session["username"] = userdata["username"][0]
            session["cookie"] = userdata["cookie"][0]
            session["year"] = userdata["year"][0]
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
            filename = '.data/' + userdata["username"][0] + '_' + userdata["year"][0] + '_history_' + st + '.csv'
            session["filename"] = filename
            results = process_result.get_users_results(userdata["username"][0], userdata["cookie"][0], int(userdata["year"][0]))
            if not results:
                return render_template("loginerror.html")
            csv_output, stats = results
            header, rows = csv_output
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(header)
                for row in rows:
                    writer.writerow(row)
            print("--- Runtime: %s minutes ---" % ((time.time() - start_time)/60))
            stats["year"] = userdata["year"][0]
            return render_template("results.html", data=stats)
        except:
            traceback.print_exc()
            return render_template("error.html")
    else:
        return render_template("error.html")

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
