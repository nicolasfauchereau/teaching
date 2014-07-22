import os, sys
import datetime
from git import Repo

import cdms2
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

from netCDF4 import Dataset


def main():
    script = sys.argv[0]
    u_file = sys.argv[1]
    u_var = sys.argv[2]
    v_file = sys.argv[3]
    v_var = sys.argv[4]
    outfile_name = sys.argv[5]

    u_data, ufile_atts = read_data(u_file, u_var)
    v_data, vfile_atts = read_data(v_file, v_var)

    wsp_data = calc_wsp(u_data, v_data)

    write_output(wsp_data, ufile_atts, outfile_name)


def read_data(ifile, var):
    """Read data from ifile corresponding to the var variable"""

    fin = cdms2.open(ifile)
    data = fin(var)
    file_atts = fin.attributes
    fin.close()

    return data, file_atts


def calc_wsp(uwnd, vwnd):
    """Calculate the wind speed and create relevant attributes"""

    wsp = (uwnd**2 + vwnd**2)**0.5

    wsp.id = 'wsp'
    wsp.long_name = 'Wind speed'
    wsp.units = 'm s-1'

    return wsp


def write_output(wsp_data, ufile_atts, outfile_name):
    """Write the output file"""

    outfile = cdms2.open(outfile_name, 'w')

    new_history = create_history()
    old_history = ufile_atts['history']

    setattr(outfile, 'history', """%s\n%s""" %(new_history, old_history))
    for att_name in ufile_atts.keys():
        if att_name != "history":  # history excluded because we've already done it
            setattr(outfile, att_name, ufile_atts[att_name])

    outfile.write(wsp_data)
    outfile.close()

def write_output_netCDF4(data, varname, time, units, calendar, lats, lons, outfile_name):
    """
    example:

    >> write_output_netCDF4(wsp_data, 'wind_speed', time, 'days since 1-01-01\
    ... 00:00:00', 'proleptic_gregorian', lats, lons, 'wsp_data.nc')
    """

    outfile = Dataset(outfile_name, 'w', format='NETCDF4')

    # dimensions
    outfile.createDimension('time', None)
    outfile.createDimension('lat', len(lats))
    outfile.createDimension('lon', len(lons))

    # variables and their attributes
    times = outfile.createVariable('time', 'f8', ('time',))
    times.units = units
    times.calendar = calendar
    latitudes = outfile.createVariable('latitude', 'f4', ('lat',))
    latitudes.units = 'degrees_north'
    longitudes = outfile.createVariable('longitude', 'f4', ('lon',))
    longitudes.units = 'degrees_east'
    var = outfile.createVariable(varname, 'f4', ('time', 'lat', 'lon',))

    # populates the netcdf variables with numpy arrays
    latitudes[:] = lats
    longitudes[:] = lons
    var[:,:,:] = data
    times[:] = time
    outfile.close()


def create_history():
    """Create the new entry for the global history file attribute"""

    time_stamp = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    exe = sys.executable
    args = " ".join(sys.argv)
    git_hash = Repo(os.getcwd()).head.commit.hexsha

    return """%s: %s %s (Git hash: %s)""" %(time_stamp, exe, args, git_hash[0:7])


main()
