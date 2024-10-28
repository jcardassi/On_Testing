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


samplingperiod = 0.1
duration = 120
active = True
start_time = None
xdata, i_data = [], []


def signal_handler(sig, frame):
    print('\n\nExiting, Bye!\n\n')
    global active
    active = False


signal.signal(signal.SIGINT, signal_handler)

PowerMeterBrand = POWERMETER.NoPowerMeter

rm = pyvisa.ResourceManager()
try:
    powermeter = rm.open_resource('ASRL3::INSTR',
                                   baud_rate=9600,
                                   data_bits=7,
                                   parity=pyvisa.constants.Parity.even,
                                   stop_bits=pyvisa.constants.StopBits.two,
                                   write_termination='\n',
                                   read_termination='\n')

    PowerMeterBrand = POWERMETER.Agilent
#    powermeter.timeout = 5000

except pyvisa.VisaIOError:
    print(f"{bcolors.FAIL}Can't connect to Agilent{bcolors.ENDC}")
    sys.exit(1)

print(powermeter.query('*IDN?'))

if PowerMeterBrand == POWERMETER.Agilent:
    powermeter.write(':SYST:REM')  # Coloca o multímetro em modo remoto
    powermeter.write(':CONF:CURR:AC 10')  # Configura medição de corrente AC


def plot_graphs(display_area):
    global active, xdata, start_time, i_data

    fig = Figure(figsize=(10, 5), dpi=110)
    ax = fig.add_subplot(111)
    i_line, = ax.plot(xdata, i_data, color='b', label='Irms')
    ax.set_xlim(0, duration)
    ax.set_ylim(0, 10)
#    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Current (i)')
    ax.set_title('SX-360 Seal + Vacuum Seal - Green Light ')
    ax.legend()

    # Configuração dos ticks do eixo X como uma régua
    major_ticks = range(0, duration + 1, 60)  # Marcadores grandes a cada minuto
    minor_ticks = range(0, duration + 1, 1)  # Marcadores pequenos a cada segundo

    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)

    # Definindo o tamanho dos ticks
    ax.tick_params( axis='x', which='major', length=8, color='black' )  # Ticks grandes
    ax.tick_params( axis='x', which='minor', length=2, color='black' )  # Ticks pequenos

#    ax.grid( True, which='both', axis='x', linestyle='--', color='gray', alpha=0.7 )

    canvas = FigureCanvasTkAgg(fig, master=display_area)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_graphs():
        global active, start_time, xdata, i_data

        if not active:
            return

        current_time = time.time() - start_time
        if current_time > duration:
            return

        try:
            powermeter.write(':READ?')
            response = powermeter.read().strip()

            if response:
                i = float(response.split(',')[0])
            else:
                raise ValueError("No data received")
        except Exception as e:
            print(f"{bcolors.FAIL}Error reading data: {e}{bcolors.ENDC}")
            i = -5

        xdata.append(current_time)
        i_data.append(i)

        i_line.set_data(xdata, i_data)

        ax.set_ylim(0, max(i_data) * 1.1 if i_data else 1)

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
    display_area.place(x=400, y=40)

    plot_graphs(display_area)

    root.mainloop()


create_interface()

if powermeter:
    powermeter.close()

sys.exit(0)
