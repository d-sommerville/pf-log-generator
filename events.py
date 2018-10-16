import threading

TIMERS = []


def spawn_timer(i, fn, *args, **kwargs):
    t = threading.Timer(i, fn, args=args, kwargs=kwargs)
    TIMERS.append(t)
    t.start()


def kill_timers():
    # FIXME: is it possible that this might cause issues if a timer function is currently running?
    for t in TIMERS:
        t.cancel()

    for t in TIMERS:
        t.join()

    TIMERS.clear()
