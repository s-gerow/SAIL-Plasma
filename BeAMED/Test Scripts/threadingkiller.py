from threading import Thread, Event,active_count
import time
from random import randrange

stop_all = Event()
osc_event = Event()
pwr_event = Event()
pressure_event = Event()
DMM_event = Event()
def config(name, events: stop_all, type):
    while not stop_all.is_set():
        print(f"configuring {name}")
        time.sleep(randrange(1,5,1))
        print("1")
        time.sleep(randrange(1,3,1))
        print("2")
        time.sleep(1)
        print("3")
        type.set()
        print(f"{name} configured")
        break

things_to_configure = {osc_event: "osc", pwr_event: "pwr", pressure_event: "pressure", DMM_event: "DMM"}
def main():
    stop_threads = False
    workers = []
    for event,name in zip(things_to_configure.keys(),things_to_configure.values()):
        tmp = Thread(target=config, args=(name, stop_all, event))
        workers.append(tmp)
        tmp.start()
    '''
    while active_count() != 1:
        print(f"Threads Active: {active_count()} \n")
        for event,name in zip(things_to_configure.keys(),things_to_configure.values()):
            print(f"{name} active?:{not event.is_set()}")
        time.sleep(1)
    print(f"only thread active is main. Finis.")
    '''
    print("testin stop all")
    stop_all.set()
    for worker in workers:
        worker.
    print("finis")

if __name__ == '__main__':
    main()