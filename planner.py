from flask import Flask, render_template, request
import datetime

app = Flask(__name__)

# define the main route
@app.route('/', methods=['GET', 'POST'])
def index():
    # get the current date
    now = datetime.datetime.now()

    # if the user submits the form, get the selected date
    if request.method == 'POST':
        date = request.form['date']
        selected_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        selected_date = now

    # create a list of days for the selected month
    month_days = []
    month_start = datetime.datetime(selected_date.year, selected_date.month, 1)
    month_end = datetime.datetime(selected_date.year, selected_date.month+1, 1) - datetime.timedelta(days=1)
    for i in range((month_end - month_start).days + 1):
        day = month_start + datetime.timedelta(days=i)
        month_days.append(day)

    # render the template with the current date and the list of days
    return render_template('index.html', now=now, selected_date=selected_date, month_days=month_days)

# run the app
if __name__ == '__main__':
    app.run(debug=True)
