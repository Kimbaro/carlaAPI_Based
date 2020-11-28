import data_collection_vehicle_remote.screen_in_no_rendering_mode as dcv
import environment_config_remote.Carla_GUI as gui
import sys
import time

from threading import Thread
import threading as threading


def start_dcv():
    dcv.main()


def start_gui():
    gui.main()


if __name__ == '__main__':
    th1 = Thread(target=start_dcv, daemon=True)
    th2 = Thread(target=start_gui, daemon=True)

    th1.start()
    time.sleep(5)
    th2.start()

    th1.join()
    th2.join()

    # th1 = Process(target=start_gui)
    # th2 = Process(target=start_dcv)
    #
    # th1.start()
    # th2.start()
    # th1.join()
    # th2.join()
