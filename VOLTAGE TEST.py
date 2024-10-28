from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import pyvisa
import signal
import sys
import time

class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class POWERMETER:
    NoPowerMeter = 0
    Agilent = 1

samplingperiod = 0.01
duration = 1800
active = True
start_time = None
xdata, v_data = [], []

def signal_handler(sig, frame):
    print('\n\nExiting, Bye!\n\n')
    global active
    active = False

signal.signal(signal.SIGINT, signal_handler)

PowerMeterBrand = POWERMETER.NoPowerMeter

rm = pyvisa.ResourceManager()
try:
    powermeter = rm.open_resource('ASRL4::INSTR',  # Alterado para COM 3
                                   baud_rate=9600,
                                   data_bits=7,
                                   parity=pyvisa.constants.Parity.even,
                                   stop_bits=pyvisa.constants.StopBits.two,
                                   write_termination='\n',
                                   read_termination='\n')

    PowerMeterBrand = POWERMETER.Agilent
    powermeter.timeout = 5000

except pyvisa.VisaIOError:
    print(f"{bcolors.FAIL}Can't connect to Agilent{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETER.Agilent:
    powermeter.write(':SYST:REM')  # Coloca o multímetro em modo remoto
    powermeter.write(':CONF:VOLT:AC 240')   # Configura medição de tensão AC

def plot_graphs(display_area):
    global active, xdata, start_time, v_data

    fig = Figure(figsize=(8, 4), dpi=100)
    ax = fig.add_subplot(111)
    v_line, = ax.plot(xdata, v_data, color='r', label='Vrms')
    ax.set_xlim(0, duration)
    ax.set_ylim(0, 240)
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Volts')
    ax.set_title('Voltage Monitoring')
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=display_area)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_graphs():
        global active, start_time, xdata, v_data

        if not active:
            return

        current_time = time.time() - start_time
        if current_time > duration:
            return

        try:
            powermeter.write(':READ?')
            response = powermeter.read().strip()

            if response:
                v = float(response.split(',')[0])  # Lê apenas a tensão (primeiro valor)
            else:
                raise ValueError("No data received")
        except Exception as e:
            print(f"{bcolors.FAIL}Error reading data: {e}{bcolors.ENDC}")
            v = -5

        xdata.append(current_time)
        v_data.append(v)

        v_line.set_data(xdata, v_data)
        ax.set_ylim(0, max(v_data) * 1.1 if v_data else 1)

        canvas.draw()
        display_area.after(int(samplingperiod * 1000), update_graphs)

    start_time = time.time()
    update_graphs()

def create_interface():
    root = tk.Tk()
    root.title('TrolBist')

    root.geometry('1920x1080')

    label_trolbist = tk.Label(root, text='TrolBist', font=('Arial', 12))
    label_trolbist.place(x=10, y=10)

    label_on_testing = tk.Label(root, text='On Testing', font=('Arial', 12), bg='lightgreen')
    label_on_testing.place(x=70, y=10)

    display_area = tk.Frame(root, width=800, height=400, bg='white', relief='solid', bd=1)
    display_area.place(x=550, y=30)

    plot_graphs(display_area)

    root.mainloop()

create_interface()

if powermeter:
    powermeter.close()

sys.exit(0)




