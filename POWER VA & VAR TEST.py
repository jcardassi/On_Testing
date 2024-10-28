import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyvisa
import signal
import sys
import math
import time


samplingperiod = 1
duration = 600
active = True
start_time = None
xdata, va_data, var_data, pf_data = [], [], [], []


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    WARNING = '\033[93m'


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
except:
    print(f"{bcolors.FAIL}Can't connect to GWInstek{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETERS.GWInstek:
    powermeter.write(':INPut:MODE ACDC')
    powermeter.write(':NUMERIC:NORMAL:NUMBER 3')
    powermeter.write(':INPUT:CURRENT:AUTO ON')


def plot_graphs(display_area1, display_area2):
    global active, start_time, xdata, va_data, var_data, pf_data

    fig1 = Figure(figsize=(8, 4), dpi=95)
    ax1 = fig1.add_subplot(111)
    va_line, = ax1.plot(xdata, va_data, 'r-', label='VA')
    var_line, = ax1.plot(xdata, var_data, 'b-', label='VAR')
    ax1.set_xlim(0, duration)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Power (VA, VAR)')
    ax1.set_title('Trolbist On_Testing - Power Apparent (VA) and Reactive (VAR)')
    ax1.legend()

    fig2 = Figure(figsize=(8, 4), dpi=95)
    ax2 = fig2.add_subplot(111)
    pf_line, = ax2.plot(xdata, pf_data, 'g-', label='PF')
    ax2.set_xlim(0, duration)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Power Factor')
    ax2.set_title('Trolbist On_Testing - Power Factor (PF)')
    ax2.legend()

    canvas1 = FigureCanvasTkAgg(fig1, master=display_area1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    canvas2 = FigureCanvasTkAgg(fig2, master=display_area2)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_graphs():
        global active, start_time, xdata, va_data, var_data, pf_data

        if not active:
            return

        current_time = time.time() - start_time
        if current_time > duration:
            return

        try:
            pmeasures = powermeter.query(':NUMERIC:NORMAL:VALUE?')
            channels = pmeasures.split(',')
            Vrms = float((channels[0].split(' '))[0])
            Irms = float((channels[1].split(' '))[0])
            Pact = float((channels[2].split(' '))[0])
            if math.isnan(Vrms):
                raise Exception()

            VA = Vrms * Irms
            VAR = math.sqrt(VA ** 2 - Pact ** 2)
            PF = Pact / VA

        except:
            print(f"{bcolors.FAIL}Something went wrong while talking with PowerMeter{bcolors.ENDC}")
            Vrms = Irms = VA = VAR = PF = -5

        xdata.append(current_time)
        va_data.append(VA)
        var_data.append(VAR)
        pf_data.append(PF)

        va_line.set_data(xdata, va_data)
        var_line.set_data(xdata, var_data)
        pf_line.set_data(xdata, pf_data)

        ax1.set_ylim(0, max(max(va_data), max(var_data)) * 1.1 if va_data else 1)
        ax2.set_ylim(0, max(pf_data) * 1.1 if pf_data else 1)

        canvas1.draw()
        canvas2.draw()
        display_area1.after(samplingperiod * 1000, update_graphs)  # Chama update_graph após samplingperiod

    start_time = time.time()
    update_graphs()


def create_interface():
    root = tk.Tk()
    root.title("TrolBist Testing")

    root.geometry("1920x1080")

    label_trolbist = tk.Label(root, text="TrolBist", font=("Arial", 12))
    label_trolbist.place(x=10, y=10)

    label_on_testing = tk.Label(root, text="On_Testing", font=("Arial", 12), bg="lightgreen")
    label_on_testing.place(x=70, y=10)

    display_area1 = tk.Frame(root, width=800, height=400, bg="white", relief="solid", bd=1)
    display_area1.place(x=550, y=30)

    display_area2 = tk.Frame(root, width=800, height=400, bg="white", relief="solid", bd=1)
    display_area2.place(x=550, y=420)

    plot_graphs(display_area1, display_area2)

    root.mainloop()


create_interface()

powermeter.close()
sys.exit(0)