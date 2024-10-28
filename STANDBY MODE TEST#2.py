import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyvisa
import signal
import sys
import math
import time

samplingperiod = 1
duration = 30
active = True
start_time = None
xdata, ydata = [], []

class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class POWERMETERS:
    NoPowerMeter = 0
    GWInstek = 1


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
except pyvisa.VisaIOError:
    print(f"{bcolors.FAIL}Can't connect to GWInstek{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETERS.GWInstek:
    powermeter.write(':INPut:MODE ACDC')
    powermeter.write(':NUMERIC:NORMAL:NUMBER 3')
    powermeter.write(':INPUT:CURRENT:AUTO ON')


def plot_graphs(display_area1):
    global active, start_time, xdata, ydata

    fig1 = Figure(figsize=(8, 4), dpi=110)
    ax1 = fig1.add_subplot(111)
    line, = ax1.plot(xdata, ydata, 'b')
    ax1.set_xlim(0, duration)
    ax1.set_ylim(0.0, 1.0)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Power (W)')
    ax1.set_title('TrolBist_On-Testing - STANDBY MODE')
#    ax1.legend()

    canvas1 = FigureCanvasTkAgg(fig1, master=display_area1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_graphs():
        global active, start_time, xdata, ydata

        if not active:
            return

        current_time = time.time() - start_time
        if current_time > duration:
            active = False

            standby_power = sum(ydata) / len(ydata) if ydata else 0
            print(f'Média da Potência de Standby: {standby_power:.2f} W')
            ax1.text(0.5, 0.5, f'Standby Power: {standby_power:.2f} W',
            transform=ax1.transAxes, fontsize=12, verticalalignment='center', color='b')
            canvas1.draw()
            return  # Finaliza a execução da função

        try:
            pmeasures = powermeter.query(':NUMERIC:NORMAL:VALUE?')
            channels = pmeasures.split(',')
            Vrms = float((channels[0].split(' '))[0])
            Irms = float((channels[1].split(' '))[0])
            Pact = float((channels[2].split(' '))[0])
            if math.isnan(Vrms):
                raise ValueError("Vrms is NaN")

        except (ValueError, pyvisa.VisaIOError) as e:
            print(f"{bcolors.FAIL}Something went wrong while talking with PowerMeter: {e}{bcolors.ENDC}")
            Pact = -5

        xdata.append(current_time)
        ydata.append(Pact)

        line.set_data(xdata, ydata)

        ax1.set_ylim(0, max(ydata) * 1.1 if ydata else 1)

        canvas1.draw()
        display_area1.after(samplingperiod * 1000, update_graphs)

    start_time = time.time()
    update_graphs()


def create_interface():
    root = tk.Tk()
    root.title("TrolBist Testing")

    root.geometry("1920x1080")

    label_trolbist = tk.Label(root, text="TrolBist", font=("Arial", 12), fg='gray')
    label_trolbist.place(x=10, y=10)

    label_on_testing = tk.Label(root, text="On_Testing", font=("Arial", 12), bg="lightgreen")
    label_on_testing.place(x=70, y=10)

    display_area1 = tk.Frame(root, width=1000, height=500, bg="white", relief="solid", bd=1)
    display_area1.place(x=550, y=100)

    plot_graphs(display_area1)

    root.mainloop()


create_interface()

powermeter.close()
sys.exit(0)

