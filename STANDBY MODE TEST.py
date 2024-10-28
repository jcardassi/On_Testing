import pyvisa
import signal
import sys
import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    WARNING = '\033[93m'


class POWERMETERS:
    NoPowerMeter = 0
    GWInstek = 1


samplingperiod = 1
duration = 300
active = True
start_time = None


def signal_handler(sig, frame):
    print('\n\nExiting, Bye!\n\n')
    global active
    active = False


signal.signal(signal.SIGINT, signal_handler)

PowerMeterBrand = POWERMETERS.NoPowerMeter

rm = pyvisa.ResourceManager()
try:
    powermeter = rm.open_resource('TCPIP0::11.1.1.136::23::SOCKET', write_termination='\r\n', read_termination='\r\n')
    PowerMeterBrand = POWERMETERS.GWInstek
except:
    print(f"{bcolors.FAIL}Can't connect to GWInstek{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETERS.GWInstek:
    powermeter.write(':INPut:MODE ACDC')
    powermeter.write(':NUMERIC:NORMAL:NUMBER 3')
    powermeter.write(':INPUT:CURRENT:AUTO ON')


fig, ax = plt.subplots()
xdata, ydata = [], []
line, = ax.plot([], [], lw=2)
standby_text = ax.text(0.85, 0.05, '', transform=ax.transAxes, fontsize=12, verticalalignment='top', color='b')
standby_power_text = ax.text(0.95, 0.01, '', transform=ax.transAxes, fontsize=12, verticalalignment='top', color='b')
plt.axhline(0.8, ls=':', color='r', label='Limite Máximo - 0.8W')
plt.legend(loc='upper right')


def init():
    global start_time
    start_time = time.time()
    ax.set_xlim(0, duration)
    ax.set_ylim(0, 2)
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Power (W)')
    ax.set_title('Power Measurement - 1720036 H&T')
    return line, standby_text, standby_power_text


def update(frame):
    global active, start_time
    if not active:
        return line, standby_text, standby_power_text

    current_time = time.time() - start_time
    if current_time > duration:
        active = False

        standby_power = sum(ydata) / len(ydata) if ydata else 0
        standby_text.set_text(f'Standby Power: {standby_power:.2f} W')
        return line, standby_text, standby_power_text

    try:
        pmeasures = powermeter.query(':NUMERIC:NORMAL:VALUE?')
        channels = pmeasures.split(',')
        Vrms = float((channels[0].split(' '))[0])
        Irms = float((channels[1].split(' '))[0])
        Pact = float((channels[2].split(' '))[0])
        if math.isnan(Vrms):
            raise Exception()
    except:
        print(f"{bcolors.FAIL}Something went wrong while talking with PowerMeter{bcolors.ENDC}")
        Vrms = -5
        Irms = -5
        Pact = -5

    xdata.append(current_time)
    ydata.append(Pact)
    line.set_data(xdata, ydata)

    return line, standby_text, standby_power_text


ani = FuncAnimation(fig, update, frames=int(duration / samplingperiod),
                    init_func=init, blit=True, repeat=False, interval=samplingperiod * 1000)

plt.show()

powermeter.close()
sys.exit(0)
