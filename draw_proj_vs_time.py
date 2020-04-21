import csv, datetime, sys, glob
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from player import Player


if len(sys.argv) < 2:
    print("Usage: python draw_proj_vs_time.py [location]")
    sys.exit()

req_location = sys.argv[1]
print("Getting data for location", req_location)
if req_location == 'United States of America': req_location = 'US'
if req_location == 'United States': req_location = 'US'

start_date = datetime.datetime(2020, 3, 1)
end_date = datetime.datetime(2020, 5, 1)

projections = []
actuals = ()
actuals_date = datetime.datetime(2020, 1, 1) # just an old date

dirs = sorted(glob.glob('2020_*_*'))
proj_dates = []
for data_dir in dirs:
    data_date = data_dir.split('.')[0]
    data_date = datetime.datetime(*[int(x) for x in data_date.split('_')])
    print("Loading", data_date)

    dates = []
    deaths_mean = []
    deaths_lower = []
    deaths_upper = []
    filename = glob.glob(data_dir+'/*.csv')[0]
    with open(filename) as csvfile:
        csv_data = csv.DictReader(csvfile)
        for row in csv_data:
            location_name = row['location_name']
            if location_name == 'United States of America': location_name = 'US'
            if location_name == 'United States': location_name = 'US'
            if location_name == req_location:
                date_name = 'date' if 'date' in row else 'date_reported'
                row_date = datetime.datetime(*[int(x) for x in row[date_name].split('-')])
                if row_date >= start_date and row_date <= end_date:
                    dates.append(row_date)
                    deaths_mean.append(float(row['totdea_mean']))
                    deaths_lower.append(float(row['totdea_lower']))
                    deaths_upper.append(float(row['totdea_upper']))

                if row_date == data_date + datetime.timedelta(days=1): 
                    if row_date > actuals_date: actuals = (dates.copy(), deaths_mean.copy())

    if len(dates) == 0: continue
    projections.append( (dates.copy(), deaths_mean.copy(), deaths_lower.copy(), deaths_upper.copy()) )
    proj_dates.append(data_date)

if len(projections) == 0:
    print("Didn't find any data for location", req_location)
    sys.exit()

fig, ax = plt.subplots()
dates, deaths_mean, deaths_lower, deaths_upper = projections[0]
bands = plt.fill_between(dates, deaths_lower, deaths_upper, alpha=0.2)
line, = plt.plot(dates, deaths_mean, '-', label='IHME prediction')
y_marker = np.interp(proj_dates[0].timestamp(), [i.timestamp() for i in dates], deaths_mean)
marker, = plt.plot(proj_dates[0], y_marker, marker='*', c='red', label='prediction date')
act, = plt.plot(actuals[0], actuals[1], '-', c='black', label='actual')
plt.gcf().autofmt_xdate()
plt.ylabel('deaths')
plt.legend(loc='upper left')
plt.title(req_location)

def update(frame):
    frame = int(frame)
    if frame < 0 or frame >= len(projections):
        print("frame", frame, "is out of range...")
        if frame < 0: frame = 0
        if frame >= len(projections): frame = len(projections)-1
        return
    dates, deaths_mean, deaths_lower, deaths_upper = projections[int(frame)]
    new_bands = plt.fill_between(dates, deaths_lower, deaths_upper, alpha=0.2)
    verts = [ path._vertices for path in new_bands.get_paths() ] 
    codes = [ path._codes for path in new_bands.get_paths() ] 
    new_bands.remove()
    bands.set_verts_and_codes(verts, codes)
    line.set_xdata(dates)
    line.set_ydata(deaths_mean)
    x_marker = proj_dates[int(frame)]
    marker.set_xdata(x_marker)
    y_marker = np.interp(x_marker.timestamp(), [i.timestamp() for i in dates], deaths_mean)
    marker.set_ydata(y_marker)
    plt.draw()

ani = Player(fig, update, mini=0, maxi=len(projections)-1, frames = len(projections), interval=500)
out_name = req_location.replace(' ', '_')+'.gif'
#ani.save(out_name, writer='imagemagick', fps=2)
plt.show()
