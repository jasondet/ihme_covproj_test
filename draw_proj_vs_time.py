import csv, datetime, sys, glob
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from player import Player

# this sets the limits of the x-axis
start_date = datetime.datetime(2020, 3, 1)
end_date = datetime.datetime(2020, 5, 1)

# if no args: print help info
if len(sys.argv) < 2:
    print("Usage: python draw_proj_vs_time.py (-s) [location]")
    print("  -s : save an animated gif instead of running interactively")
    print("Note: if the location name has a space, enclose the name in quotes.")
    print('Example: python draw_proj_vs_time.py "New York"')
    sys.exit()

# process arguments
save_gif = True if sys.argv[1] == '-s' else False
req_location = sys.argv[1 + int(save_gif)]

# location name mangling
print("Getting data for location", req_location)
if req_location == 'United States of America': req_location = 'US'
if req_location == 'United States': req_location = 'US'

# set up variables for the data import loop
projections = []
actuals = ()
actuals_date = datetime.datetime(2020, 1, 1) # just an old date

# find all available data
dirs = sorted(glob.glob('data/2020_*_*'))
proj_dates = []
for data_dir in dirs:
    # parse the date of the projection out of the directory name 
    data_date = data_dir.split('/')[-1].split('.')[0]
    data_date = datetime.datetime(*[int(x) for x in data_date.split('_')])
    print("Loading", data_date)

    # prepare variables for loop over data file
    dates = []
    deaths_mean = []
    deaths_lower = []
    deaths_upper = []
    filename = glob.glob(data_dir+'/*.csv')[0]
    with open(filename) as csvfile:
        csv_data = csv.DictReader(csvfile)
        # read data row-by-row and look for the requested location
        for row in csv_data:
            # handle location name changes in IHME's data
            location_name = row['location_name']
            if location_name == 'United States of America': location_name = 'US'
            if location_name == 'United States': location_name = 'US'

            # load data for requested location when found 
            if location_name == req_location:
                # column naming change in IHME's data
                date_name = 'date' if 'date' in row else 'date_reported'

                # get the date corresponding to this row
                row_date = datetime.datetime(*[int(x) for x in row[date_name].split('-')])

                # load data if within the desired date range for plotting 
                if row_date >= start_date and row_date <= end_date:
                    dates.append(row_date)
                    deaths_mean.append(float(row['totdea_mean']))
                    deaths_lower.append(float(row['totdea_lower']))
                    deaths_upper.append(float(row['totdea_upper']))

                # update actuals so that we end up with the most recent result
                if row_date == data_date + datetime.timedelta(days=1): 
                    if row_date > actuals_date: actuals = (dates.copy(), deaths_mean.copy())

    # add this projetion's data to our lists, if there is any
    if len(dates) == 0: continue
    projections.append( (dates.copy(), deaths_mean.copy(), deaths_lower.copy(), deaths_upper.copy()) )
    proj_dates.append(data_date)

# exit if the requested location was not found
if len(projections) == 0:
    print("Didn't find any data for location", req_location)
    sys.exit()

# draw the starting plot. Use the most recent projection (index = -1) so that
# the y-range auto-scales to the most relevant range
fig, ax = plt.subplots()
dates, deaths_mean, deaths_lower, deaths_upper = projections[-1]

# the uncertainty bands - draw them first, beneath everything
bands = plt.fill_between(dates, deaths_lower, deaths_upper, alpha=0.2)

# the best-guess projection
line, = plt.plot(dates, deaths_mean, '-', label='IHME prediction')

# add a marker for the data the projection was made
y_marker = np.interp(proj_dates[-1].timestamp(), [i.timestamp() for i in dates], deaths_mean)
marker_label='predicted '+proj_dates[-1].date().isoformat()
marker, = plt.plot(proj_dates[-1], y_marker, marker='*', c='red', linestyle='None', label=marker_label)
act, = plt.plot(actuals[0], actuals[1], '-', c='black', label='actual')

# pretty up the plot: title, axes, legend
plt.gcf().autofmt_xdate()
plt.ylabel('deaths')
legend = plt.legend(loc='upper left')
plt.title(req_location)

# update function for animation loop
def update(frame):
    # "frame" is the index in the projections list
    frame = int(frame)
    if frame < 0 or frame >= len(projections):
        print("frame", frame, "is out of range...")
        if frame < 0: frame = 0
        if frame >= len(projections): frame = len(projections)-1
        return

    # pull out data for this frame
    dates, deaths_mean, deaths_lower, deaths_upper = projections[int(frame)]

    # update the uncertainty bands
    new_bands = plt.fill_between(dates, deaths_lower, deaths_upper, alpha=0.2)
    verts = [ path._vertices for path in new_bands.get_paths() ] 
    codes = [ path._codes for path in new_bands.get_paths() ] 
    new_bands.remove()
    bands.set_verts_and_codes(verts, codes)

    # update best-guess projection
    line.set_xdata(dates)
    line.set_ydata(deaths_mean)

    # update projection date marker and its label
    x_marker = proj_dates[int(frame)]
    marker.set_xdata(x_marker)
    y_marker = np.interp(x_marker.timestamp(), [i.timestamp() for i in dates], deaths_mean)
    marker.set_ydata(y_marker)
    marker_label='predicted '+proj_dates[frame].date().isoformat()
    legend.get_texts()[1].set_text(marker_label)

    # update plot
    plt.draw()

# start from the first projection
update(0)

# set up the player
ani = Player(fig, update, mini=0, maxi=len(projections)-1, frames = len(projections), interval=500)

# save an animated gif or go interactive
if save_gif: 
    out_name = req_location.replace(' ', '_')+'.gif'
    ani.save(out_name, writer='imagemagick', fps=2)
else: plt.show()
