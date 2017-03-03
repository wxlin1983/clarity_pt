import signal
import time
import os

import clarity_ptlib

import numpy as np
import matplotlib.pyplot as plt

from os.path import expanduser
from PyDAQmx import *

# Options
OutputDiagnosis = True
ShowFigure = False

# Set folder and file names
home = expanduser("~")
filefolder = home + \
    '\\Dropbox (Clarity Movement)\\Hardware R&D\\P1 sensor\\Calibration\\2017_02_27_MVP test\\'
filefolder = '.\\'
filename1 = 'mvp_1707-00010oldpd'
filename2 = 'mvp_1707-00010newpd'

# Generate output fieldnames
cla_fn = clarity_ptlib.cla_makefieldnames()

# Create new folder for raw data
filefoldertmp = filefolder + 'raw data - ' + \
    str(int(round(time.time()))) + '\\'
if not os.path.exists(filefoldertmp):
    os.makedirs(filefoldertmp)
filefolder = filefoldertmp

# Handle Ctrl-C event
intr = False


def signal_handler(signal, frame):
    # print('Ctrl-C pressed!')
    global intr
    intr = True
signal.signal(signal.SIGINT, signal_handler)

# Set DAQ settings
nChan = 2
nSample = 50000
fSample = 50000
nAcquisition = 20

# Preparing buffer
taskHandle = TaskHandle()
read = int32()
data = np.zeros((nChan * nSample,), dtype=np.float64)

filecounter = 0
try:

    print('Start data acquisition.')
    print('To avoid loss of data, press Ctrl-C if you wish to terminate the program earlier.')
    # Configure DAQmx
    DAQmxCreateTask("", byref(taskHandle))
    DAQmxCreateAIVoltageChan(taskHandle, b'Dev2/ai0:1',
                             "", DAQmx_Val_Diff, 0, 5, DAQmx_Val_Volts, None)
    DAQmxCfgSampClkTiming(taskHandle, "", fSample,
                          DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, nSample)

    data0list = []
    data1list = []
    headerlist = []
    for ii in range(nAcquisition):

        print('Taking data: ', ii + 1, ' of ', nAcquisition)

        # Start DAQmx
        timestamp = time.time() + 0.5
        DAQmxStartTask(taskHandle)
        DAQmxReadAnalogF64(taskHandle, nSample, nSample / fSample + 1,
                           DAQmx_Val_GroupByChannel, data, nSample * nChan, byref(read), None)
        DAQmxStopTask(taskHandle)

        # Convert voltage to 16-bits integer
        dataint = clarity_ptlib.niv2i(data).astype(int16)

        # Create 15-bits histogram (only the positive half of 16-bits are used)
        [data0, data1] = np.split(dataint, 2)
        header, data0hist = clarity_ptlib.mkhist(
            data0, diagnosis=OutputDiagnosis, timestamp=timestamp)
        header, data1hist = clarity_ptlib.mkhist(
            data1, diagnosis=OutputDiagnosis, timestamp=timestamp)

        data0list.append(data0hist)
        data1list.append(data1hist)
        headerlist.append(header)

        if len(headerlist) >= 1200:
            print('Flush buffer to files.')
            np.save(filefolder + filename1 + '_hist_' +
                    clarity_ptlib.str3(filecounter) + '.npy', np.array(data0list))
            np.save(filefolder + filename2 + '_hist_' +
                    clarity_ptlib.str3(filecounter) + '.npy', np.array(data1list))
            np.save(filefolder + filename1 + '_header_' +
                    clarity_ptlib.str3(filecounter) + '.npy', np.array(headerlist))
            np.save(filefolder + filename2 + '_header_' +
                    clarity_ptlib.str3(filecounter) + '.npy', np.array(headerlist))
            data0list = []
            data1list = []
            headerlist = []
            filecounter = filecounter + 1

        # Break the loop if user interrupt
        if intr:
            print('User interrupted.')
            break

except DAQError as err:
    print("DAQmx Error Code: ", err.error)

finally:
    if taskHandle:
        print('Finished Acquisition.')
        # Stop DAQmx
        DAQmxClearTask(taskHandle)

if len(headerlist) != 0:
    print('Flush buffer to files.')
    np.save(filefolder + filename1 + '_hist_' + clarity_ptlib.str3(filecounter) +
            '.npy', np.array(data0list))
    np.save(filefolder + filename2 + '_hist_' + clarity_ptlib.str3(filecounter) +
            '.npy', np.array(data1list))
    np.save(filefolder + filename1 + '_header_' + clarity_ptlib.str3(filecounter) +
            '.npy', np.array(headerlist))
    np.save(filefolder + filename2 + '_header_' + clarity_ptlib.str3(filecounter) +
            '.npy', np.array(headerlist))