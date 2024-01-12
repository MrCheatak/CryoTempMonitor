import datetime
import math
import timeit

import pyvisa
import time
import threading


class Session(threading.Thread):
    def __init__(self, file, parent):
        threading.Thread.__init__(self)
        self.file = file
        self.parent = parent
        self.f = None
        self.data = []
        self.alive = True

        self.connect_to_device()
        self.reset_device()
        # self.prepare_plot_plotly()
        self.prepare_plot()

    def prepare_plot(self):
        """
        Initialize the monitoring plot.
        :return:
        """
        self.f = self.parent.show_plot()

    def update_plot(self, x, y):
        """
        Add a new point to the monitoring plot and update it.
        :param x: point x
        :param y: point y
        :param y:
        :return: -1 if plotting window is closed, 0 otherwise
        """
        # Checking if plotting window is open
        if self.f.isVisible() is False:
            self.alive = False
            return -1
        x_data, y_data = self.f.lines.get_data()
        x_data.append(x)
        # Updating x-axis range
        if type(x) is datetime.datetime:
            delta = x - x_data[0]
            if delta.seconds/60/60 > 1:
                delta = datetime.timedelta(seconds=3600)
                margin = datetime.timedelta(seconds=180)
                self.f.ax.set_xlim(x-delta-margin, x+margin)
        y_data.append(y)
        # Updating data
        self.f.lines.set_data(x_data, y_data)
        self.f.lines.set_data((x_data,y_data))
        # Updating heating speed value
        i = len(x_data)
        step = 50
        if i > step:
            try:
                heating_speed = (y_data[i-1] - y_data[i-step-1]) / (x_data[i-1] - x_data[i-step-1]).seconds * 60
                text = f'Heating speed: {heating_speed:.2f} ⁰C/min'
                self.f.heating_speed.set_text(text)
            except IndexError:
                pass
        # Finishing update
        self.f.ax.relim()
        self.f.ax.autoscale_view()
        self.f.canvas.draw()
        return 0

    def connect_to_device(self, n=0):
        """
        Find available devices and connect to one of them
        :param n: index of the device
        :return:
        """
        rm = pyvisa.ResourceManager()
        devs = rm.list_resources()
        print(f'Found devices: {devs}')
        try:
            self.smu = rm.open_resource(devs[n])
        except IndexError:
            print('No device found. Please connect one.')
            return

        print(f'Connected to {devs[0]}')

    def run(self):
        """
        Run the monitoring
        :return:
        """
        self.alive = True
        if self.file:
            f = open(self.file, 'w')
            f.write("#measurement started at " + str(time.ctime()) + " with Keithley 2636A \n")
            f.writelines(["# Time \t t ( s ) \t R ( Ohm )  \t T (C)\n"])
        self.setup_device()

        # Read the resistance measurement
        self.smu.write('smua.source.output = smua.OUTPUT_ON')

        start = timeit.default_timer()
        while self.alive:
            t = timeit.default_timer() - start
            # Getting resistance measurement
            self.smu.write('print(smua.measure.r())')
            response = self.smu.read()
            resistance = float(response.strip())
            print(f'Resistance: {resistance:.2f} Ohms', end='\t')
            T = - (math.sqrt(-0.00232 * resistance + 17.59246) - 3.908) / 0.00116
            print(f' Temperature: {T:.2f} deg. C')
            time.sleep(0.05)
            date = datetime.datetime.now()
            if self.file:
                f.writelines([date.strftime('%H:%M:%S.%f'), '\t', f'{t:.3f}', '\t', f'{resistance:.3f}', '\t', f'{T:.3f}', '\n'])
            self.data.append([date, T])
            self.update_plot(date, T)
        print('Finished')
        if self.file:
            f.close()
        self.smu.write('smua.source.output = smua.OUTPUT_OFF')
        self.parent.finished(True, 'Closed plotting window')

    def setup_device(self):
        """
        Set up the device for measurement
        :return:
        """
        self.smu.write('*RST')
        self.smu.write('smua.reset()')
        self.smu.write('smua.source.func = smua.OUTPUT_DCAMPS')
        self.smu.write('smua.source.leveli = 1e-3')
        self.smu.write('smua.measure.autorangev = smua.AUTORANGE_ON')
        self.smu.write('smua.measure.nplc = 5')
        self.smu.write('smua.measure.delay = 0.1')
        self.smu.write('smua.measure.rangev = 20')
        self.smu.write('smua.measure.rangei = 1e-3')
        self.smu.write('smua.measure.r(smua.nvbuffer1)')

    def reset_device(self):
        """
        Reset the device to the default state
        :return:
        """
        self.smu.write("smua.reset()")
        self.smu.write("smua.source.func = smua.OUTPUT_DCVOLTS")
        self.smu.write(f"smua.source.levelv = 0.0")
        self.smu.write("smua.source.autorangev = smua.AUTORANGE_ON")
        self.smu.write("smua.measure.autorangei = smua.AUTORANGE_ON")
        self.smu.write("smua.source.output = smua.OUTPUT_OFF")

    def finish(self):
        """
        Finish monitoring
        :return:
        """
        self.alive = False

    def __del__(self):
        self.reset_device()
        self.smu.close()

if __name__ == '__main__':
    # Usage: Create an instance of Session and start the measurement
    pass
