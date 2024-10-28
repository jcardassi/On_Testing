import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyvisa
import signal
import sys
import math
import time


samplingperiod = 0.1
duration = 120
active = True
start_time = None
xdata, v_data, i_data = [], [], []


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
except Exception as e:  # Corrigido para capturar a exceção corretamente
    print(f"{bcolors.FAIL}Can't connect to GWInstek: {str(e)}{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETERS.GWInstek:
    try:
        powermeter.write(':INPut:MODE ACDC')
        powermeter.write(':NUMERIC:NORMAL:NUMBER 3')
        powermeter.write(':INPUT:CURRENT:AUTO ON')

    except Exception as e:
        print(f"{bcolors.FAIL}Error initializing PowerMeter: {str(e)}{bcolors.ENDC}")
        sys.exit(1)


def plot_graphs(display_area1, display_area2):
    global active, start_time, xdata, v_data, i_data

    fig1 = Figure(figsize=(8, 4), dpi=100)
    ax1 = fig1.add_subplot(111)
    v_line, = ax1.plot(xdata, v_data, 'r-', label='Voltage (Vrms)')
    ax1.set_xlim(0, duration)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('VOLTAGE')
    ax1.set_title('Trolbist On_Testing - VOLTAGE MEASUREMENT (AC)')
    ax1.legend()

    fig2 = Figure(figsize=(8, 4), dpi=100)
    ax2 = fig2.add_subplot(111)
    i_line, = ax2.plot(xdata, i_data, 'b-', label='Current (Irms)')
    ax2.set_xlim(0, duration)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('CURRENT')
    ax2.set_title('Trolbist On_Testing - CURRENT MEASUREMENT (AC)')
    ax2.legend()

    canvas1 = FigureCanvasTkAgg(fig1, master=display_area1)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    canvas2 = FigureCanvasTkAgg(fig2, master=display_area2)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_graphs():
        global active, start_time, xdata, v_data, i_data

        if not active:
            return

        current_time = time.time() - start_time
        if current_time > duration:
            return

        try:
            pmeasures = powermeter.query(':NUMERIC:NORMAL:VALUE?')
            print(f"Resposta do medidor: {pmeasures}")
            channels = pmeasures.split(',')

            v = float(channels[0])
            i = float(channels[1])

            if math.isnan(v) or math.isnan(i):
                raise ValueError("Valores de tensão ou corrente inválidos")

        except Exception as e:
            print(f"{bcolors.FAIL}Something went wrong while talking with PowerMeter: {str(e)}{bcolors.ENDC}")
            return

        xdata.append(current_time)
        v_data.append(v)
        i_data.append(i)

        v_line.set_data(xdata, v_data)
        i_line.set_data(xdata, i_data)

        ax1.set_ylim(0, max(v_data) * 1.1 if v_data else 1)
        ax2.set_ylim(0, max(i_data) * 1.1 if i_data else 1)

        canvas1.draw()
        canvas2.draw()
        display_area1.after(int(samplingperiod * 1000), update_graphs)

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
    display_area1.place(x=450, y=10)

    display_area2 = tk.Frame(root, width=800, height=400, bg="white", relief="solid", bd=1)
    display_area2.place(x=450, y=415)

    plot_graphs(display_area1, display_area2)

    root.mainloop()


create_interface()

powermeter.close()
sys.exit(0)











