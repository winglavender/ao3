from flask import Flask
from flask import render_template
from flask import request
from flask import send_file
import process_result
import csv
import time
import datetime

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        userdata = dict(request.form)
        username = userdata["username"][0]
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
        filename = 'data/history_' + st + '.csv'
        try:
            header, rows = process_result.get_users_results(userdata["username"][0], userdata["cookie"][0], int(userdata["year"][0]))
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(header)
                for row in rows:
                    writer.writerow(row)
            return send_file(filename, as_attachment=True)
        except Error as e:
            return("ERROR")
    else:
        return("ERROR")

if __name__ == "__main__":
    app.run(debug=True)
    #app.run()
