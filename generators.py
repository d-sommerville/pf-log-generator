#!/usr/bin/python3.5 -p

import time
import threading
import uuid
import math
import signal
import sys
from random import random, randint, choice
from functools import reduce

import util
import constants
import events
from cache import TimedCache
from logging import LogWriter

# Create a timed cache for each host to track recent transactions
RECENT_TRANSACTION_CACHE_BY_HOST = {h: TimedCache(constants.OAuth.TXN_CACHE_TTL) for h in util.Mock.HOSTS}

CPU_USAGE_BY_HOST = {h: randint(constants.Cpu.MIN_BASE_USAGE, constants.Cpu.MAX_BASE_USAGE) for h in util.Mock.HOSTS}
MEMORY_USAGE_BY_HOST = {h: randint(constants.Memory.MIN_BASE_USAGE, constants.Memory.MAX_BASE_USAGE) for h in util.Mock.HOSTS}
DISK_USAGE_BY_HOST = {h: randint(constants.Disk.MIN_BASE_USAGE, constants.Disk.MAX_BASE_USAGE) for h in util.Mock.HOSTS}

LOGGERS = {}
OS_METRIC_THREADS = {}
# XXX: should this be individual to each class?
LOCK = threading.Lock()


# TODO: create package/setup and move run code into __main__ module
# XXX: can this be reworked to also be extended by LogWriter?
class LogGenerator(threading.Thread):

    THREADS = []

    def __init__(self):
        threading.Thread.__init__(self)
        self.thread_id = uuid.uuid4()
        self._stop_event = threading.Event()
        self.setDaemon(True)

    def run(self):
        print("Starting thread %s" % self.thread_id)
        while not self._stop_event.is_set():
            try:
                self._generate()
            except Exception as e:
                print(e)
            time.sleep(1)

    def stop(self):
        self._stop_event.set()

    def _generate(self):
        pass

    @classmethod
    def spawn_threads(cls, count, lifetime=0):
        """
        Spawn additional OAuthTransactionGenerator threads.

        :param count: Number of threads to spawn.
        :param lifetime: If a lifetime greater than 0 is given, automatically kills the
                         spawned threads after lifetime seconds Defaults to 0.
        """
        for n in range(count):
            cls()
            time.sleep(random() * 2)  # Stagger threads

        if lifetime > 0:
            events.spawn_timer(lifetime, cls.kill_threads, count)

    @classmethod
    def kill_threads(cls, count=0):
        count = len(cls.THREADS) if count <= 0 else count
        killed_threads = []

        for n in range(count):
            t = cls.THREADS.pop()
            t.stop()
            killed_threads.append(t)

        for t in killed_threads:
            t.join()
            print("Stopped %s thread %s" % (cls.__name__, str(t.thread_id)))


class OSLogGenerator(LogGenerator):

    THREADS = []
    DISK_USAGE_LOGGER = None
    CPU_USAGE_LOGGER = None
    MEMORY_USAGE_LOGGER = None

    def __init__(self, host):
        LogGenerator.__init__(self)
        self.host = host
        OSLogGenerator.THREADS.append(self)
        self._init_loggers()
        self.start()

    @staticmethod
    def _init_loggers():
        if OSLogGenerator.DISK_USAGE_LOGGER is None:
            OSLogGenerator.DISK_USAGE_LOGGER = LOGGERS.get(constants.Logs.DISK_USAGE_LOG)
        if OSLogGenerator.CPU_USAGE_LOGGER is None:
            OSLogGenerator.CPU_USAGE_LOGGER = LOGGERS.get(constants.Logs.CPU_USAGE_LOG)
        if OSLogGenerator.MEMORY_USAGE_LOGGER is None:
            OSLogGenerator.MEMORY_USAGE_LOGGER = LOGGERS.get(constants.Logs.MEMORY_USAGE_LOG)

    def run(self):
        print("Starting OS log thread %s" % self.thread_id)
        while not self._stop_event.is_set():
            try:
                self._generate()
            except Exception as e:
                print(e)
            time.sleep(constants.OS_METRIC_GENERATION_INTERVAL)

    def stop(self):
        self._stop_event.set()

    def disk_cleanup(self):
        DISK_USAGE_BY_HOST[self.host] = randint(constants.Disk.MIN_BASE_USAGE, constants.Disk.MAX_BASE_USAGE)
        events.spawn_timer(3600 * 2, self.disk_cleanup)  # Recurring cleanup every 2 hours

    def _generate(self):
        df_entry = self._df_entry()  # TODO: mock FS/disk size/mount path for multiple disks on each host
        cpu_entry = self._cpu_entry(nice=random() * constants.Cpu.NICE_MAX,
                                    system=random() * constants.Cpu.SYS_MAX,
                                    wait=random() * constants.Cpu.WAIT_MAX)
        mem_entry = self._mem_entry()
        OSLogGenerator.DISK_USAGE_LOGGER.write(df_entry)
        OSLogGenerator.CPU_USAGE_LOGGER.write(cpu_entry)
        OSLogGenerator.MEMORY_USAGE_LOGGER.write(mem_entry)

    def _df_entry(self, file_system=None, disk_size=None, mount_path=None):
        size = disk_size or constants.Disk.DISK_SIZE_DEFAULT
        usage_percentage = math.ceil(DISK_USAGE_BY_HOST[self.host])
        used = math.floor((usage_percentage * size) / 100)
        available_space = size - used
        # timestamp                 host                fs          size        used    avail   %used   mnt
        # 2018-09-18 20:13:16,390   solsyspingfed7		none		100G		6G		94G		6%		/
        return '%s\t\t%s\t\t%s\t\t%sG\t\t%sG\t\t%sG\t\t%s%%\t\t%s\r\n' % (
            util.timestamp(),
            self.host,
            file_system or constants.Disk.FILESYSTEM_DEFAULT,
            size,
            used,
            available_space,
            usage_percentage,
            mount_path or constants.Disk.MOUNT_PATH_DEFAULT
        )

    def _cpu_entry(self, core=None, nice=None, system=None, wait=None):
        usr = CPU_USAGE_BY_HOST[self.host]
        nice = nice or constants.Cpu.DEFAULT_NICE
        system = system or constants.Cpu.DEFAULT_SYS
        wait = wait or constants.Cpu.DEFAULT_WAIT
        # timestamp                 host              core     %usr       %nice   %sys    %wait   %idle
        # 2018-09-18 20:13:16,390   solsyspingfed1    all      31.39      0.00    9.62    5.95    53.04
        return '%s\t\t%s\t\t%s\t\t%.2f\t\t%.2f\t\t%.2f\t\t%.2f\t\t%.2f\r\n' % (
            util.timestamp(),
            self.host,
            core or constants.Cpu.ALL,
            usr,
            nice,
            system,
            wait,
            100 - (usr + nice + system + wait)
        )

    def _mem_entry(self, mem_total=None, processes=None, threads=None, interrupts=None):
        mem_used = MEMORY_USAGE_BY_HOST[self.host]
        mem_total = mem_total or constants.Memory.DEFAULT_TOTAL
        mem_free = mem_total - mem_used
        free_percentage = mem_free / mem_total * 100
        used_percentage = 100 - free_percentage
        with LOCK:
            recent_tx_count = len(RECENT_TRANSACTION_CACHE_BY_HOST[self.host].entries())
        # memTotalMB    memFreeMB   memUsedMB  memFreePct  memUsedPct   processes   threads  interrupts_PS
        # 32158         30599       1558       95.2        4.8          200         494      650.00
        return '%s\t\t%s\t\t%s\t\t%s\t\t%s\t\t%.1f\t\t%.1f\t\t%s\t\t%s\t\t%.2f\r\n' % (
            util.timestamp(),
            self.host,
            mem_total,
            mem_free,
            mem_used,
            free_percentage,
            used_percentage,
            # XXX: should these values be constants?
            processes or randint(constants.Memory.MIN_PROCESSES, constants.Memory.MAX_PROCESSES) + recent_tx_count,
            threads or randint(constants.Memory.MIN_THREADS, constants.Memory.MAX_THREADS) + recent_tx_count * 2,
            interrupts or randint(constants.Memory.MIN_INTERRUPTS, constants.Memory.MAX_INTERRUPTS)
        )

    @classmethod
    def spawn_threads(cls, count, lifetime=0):
        pass  # OS log threads are created separately so one is assigned to each host


class OAuthTransactionGenerator(LogGenerator):

    THREADS = []

    def __init__(self):
        LogGenerator.__init__(self)
        self.logger = LOGGERS.get(constants.Logs.AUDIT_LOG)
        self.tid = self.user = self.ip = self.client = self.host = self.adapter_id = None
        self.event = constants.Events.OAUTH
        self.role = constants.Roles.AS
        self.protocol = constants.Protocols.OAUTH2
        self.status = constants.Statuses.SUCCESS
        OAuthTransactionGenerator.THREADS.append(self)
        self.start()

    def _scramble(self):
        """
        Scramble the random values in the generator to mock a new transaction in the thread.
        """
        self.tid = util.Mock.tid()
        self.user = util.Mock.user()
        self.ip = util.Mock.ip_address()
        self.client = util.Mock.client()
        self.host = util.Mock.host()
        self.adapter_id = util.Mock.adapter()

    def _mock_usage(self):
        # TODO: have a timed decrease in disk usage (rollover archiving, cold storage, periodic removal etc.)
        # TODO: simulate CPU/Memory flapping?
        with LOCK:
            RECENT_TRANSACTION_CACHE_BY_HOST[self.host].add('placeholder')  # FIXME
            recent_tx_count = len(RECENT_TRANSACTION_CACHE_BY_HOST[self.host].entries())
        DISK_USAGE_BY_HOST[self.host] += constants.Disk.USAGE_INCREMENT_PER_TRANSACTION
        if DISK_USAGE_BY_HOST[self.host] >= 100:
            DISK_USAGE_BY_HOST[self.host] = 100
            # TODO: generate disk usage errors in server.log
        # wobble the base values and add a multiplier based on transactions in the last n minutes
        cpu = reduce(lambda x, y: x + random() * constants.Cpu.MAX_USAGE_PER_TRANSACTION, range(recent_tx_count), 0)
        CPU_USAGE_BY_HOST[self.host] = randint(constants.Cpu.MIN_BASE_USAGE, constants.Cpu.MAX_BASE_USAGE) + cpu
        mem = reduce(lambda x, y: x + math.ceil(random() * constants.Memory.MAX_USAGE_PER_TRANSACTION),
                     range(recent_tx_count), 0)
        MEMORY_USAGE_BY_HOST[self.host] = randint(constants.Memory.MIN_BASE_USAGE, constants.Memory.MAX_BASE_USAGE) + mem

    def run(self):
        print("Starting thread %s" % self.thread_id)
        while not self._stop_event.is_set():
            try:
                self._scramble()
                self._generate()
                self._mock_usage()
            except Exception as e:
                print(e)
            time.sleep(randint(1, 3))

    def stop(self):
        self._stop_event.set()

    @staticmethod
    def usage_curve():
        # FIXME: change this function to ramp to the expected value for the current time rather than running once a day
        events.spawn_timer(3600 * 24, OAuthTransactionGenerator.usage_curve)  # Re-run in 24 hours
        # Initial wind-up for the first few hours of the day
        windup_intervals = ((constants.Usage.PEAK_TIME - constants.Usage.KICKOFF_TIME)
                            * (60 // constants.Usage.INCREASE_INTERVAL))
        lifetime = (constants.Usage.DROPOFF_TIME - constants.Usage.KICKOFF_TIME) * 3600
        for n in range(windup_intervals):
            new_threads = randint(constants.Usage.INCREASE_VOLUME - math.floor(constants.Usage.INCREASE_VOLUME / 2),
                                  constants.Usage.INCREASE_VOLUME + math.floor(constants.Usage.INCREASE_VOLUME / 2))
            # Assign a finite lifetime to the threads so we kill them off by the end of the day
            OAuthTransactionGenerator.spawn_threads(new_threads, lifetime=lifetime)
            time.sleep(randint(constants.Usage.INCREASE_INTERVAL - math.floor(constants.Usage.INCREASE_INTERVAL / 2),
                               constants.Usage.INCREASE_INTERVAL + math.floor(constants.Usage.INCREASE_INTERVAL / 2))
                       * 60)  # Sleep a few minutes until the next interval

    @staticmethod
    def disk_overflow():
        pass  # TODO

    def _generate(self):
        self.logger.write(self._authn_start())
        time.sleep(randint(constants.OAuth.MIN_AUTHN_TIME, constants.OAuth.MAX_AUTHN_TIME))
        # XXX: should this be using a separate library to generate % failures?
        # FIXME: this function is ugly
        if random() > .90:
            self.logger.write(self._authn_failure())
            return
        self.logger.write(self._authn_success())
        if random() > .90:
            self.logger.write(self._authz_code_failure())
            return
        if random() > .92:
            time.sleep(constants.OAuth.AUTH_CODE_LIFETIME)
            self.logger.write(self._authz_code_expiry())
            return
        self.logger.write(self._authz_code_request())
        # TODO: additional failures here (incorrect credentials / redirect)
        self.logger.write(self._token_request())
        if random() > .97:
            time.sleep(constants.OAuth.ACCESS_TOKEN_LIFETIME)
            self.logger.write(self._introspection_expiry())
            return
        self.logger.write(self._introspection())
        if random() > .97:
            time.sleep(constants.OAuth.ACCESS_TOKEN_LIFETIME)
            self.logger.write(self._validation_expiry())
            return
        self.logger.write(self._validation())
        time.sleep(randint(constants.OAuth.MIN_REFRESH_TIME, constants.OAuth.MAX_REFRESH_TIME))
        if random() > .98:
            time.sleep(constants.OAuth.REFRESH_TOKEN_LIFETIME)
            self.logger.write(self._refresh_token_failure())
            return
        self.logger.write(self._refresh())

    # FIXME: all of these functions are samey; should find a way to merge them
    def _authn_start(self):
        return self._audit_entry(
            event=constants.Events.AUTHENTICATION_ATTEMPT,
            user="",
            protocol="",
            role=constants.Roles.IDP,
            status=constants.Statuses.IN_PROGRESS
        )

    def _authn_success(self):
        return self._audit_entry(
            event=constants.Events.AUTHENTICATION_ATTEMPT,
            client="",
            protocol="",
            role=constants.Roles.IDP
        )

    def _authn_failure(self):
        return self._audit_entry(
            event=constants.Events.AUTHENTICATION_ATTEMPT,
            client="",
            protocol="",
            role=constants.Roles.IDP,
            status=constants.Statuses.IN_PROGRESS
        )

    def _authz_code_request(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.AUTH_CODE
        )

    def _authz_code_failure(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.AUTH_CODE,
            status=constants.Statuses.FAILURE,
            description=choice([
                constants.Errors.INVALID_CLIENT_ID,
                constants.Errors.INVALID_SCOPE,
                constants.Errors.INVALID_SECRET
            ])
        )

    def _authz_code_expiry(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.AUTH_CODE,
            status=constants.Statuses.FAILURE,
            description=constants.Errors.AUTHZ_CODE_EXPIRED
        )

    def _token_request(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.AUTH_CODE,
            adapter_id=""
        )

    def _introspection(self):
        return self._audit_entry(
            client=constants.Clients.RS_CLIENT,
            adapter_id=""
        )

    def _introspection_expiry(self):
        return self._audit_entry(
            client=constants.Clients.RS_CLIENT,
            adapter_id="",
            status=constants.Statuses.FAILURE,
            description=constants.Errors.TOKEN_EXPIRED
        )

    def _validation(self):
        return self._audit_entry(
            client=constants.Clients.RS_CLIENT,
            grant_type=constants.GrantTypes.VALIDATE_BEARER,
            adapter_id=""
        )

    def _validation_expiry(self):
        return self._audit_entry(
            client=constants.Clients.RS_CLIENT,
            grant_type=constants.GrantTypes.VALIDATE_BEARER,
            adapter_id="",
            status=constants.Statuses.FAILURE,
            description=constants.Errors.TOKEN_EXPIRED
        )

    def _refresh(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.REFRESH,
            adapter_id=""
        )

    def _refresh_token_failure(self):
        return self._audit_entry(
            grant_type=constants.GrantTypes.AUTH_CODE,
            status=constants.Statuses.FAILURE,
            adapter_id="",
            description=constants.Errors.INVALID_REFRESH_TOKEN
        )

    def _audit_entry(
            self,
            role=None,
            event=None,
            user=None,
            client=None,
            protocol=None,
            grant_type="",
            status=None,
            adapter_id=None,
            description=""):
        response_time = util.Mock.response_time()
        time.sleep(response_time / 1000)
        timestamp = util.timestamp()
        # FIXME: this function is ugly
        return "%s| tid:%s| %s| %s| %s| %s| %s| %s| %s| %s| %s| %s| %s| %s| %s\r\n" % (
            timestamp,
            self.tid,
            event if event is not None else self.event,
            user if user is not None else self.user,
            self.ip,
            "",
            client if client is not None else self.client,
            protocol if protocol is not None else self.protocol,
            grant_type,
            self.host,
            role if role is not None else self.role,
            status if status is not None else self.status,
            adapter_id if adapter_id is not None else self.adapter_id,
            description,
            response_time
        )


def run():
    # Initialize logger threads
    # FIXME: figure out a nicer way to do this!
    for k, log in constants.Logs.__dict__.items():
        if not str(k).startswith('__') and not callable(log):
            l = LogWriter(log)
            LOGGERS[log] = l

    # Spawn transaction generation threads
    OAuthTransactionGenerator.spawn_threads(randint(constants.OAuth.TXN_MIN_THREADS, constants.OAuth.TXN_MAX_THREADS))

    # Start OS metrics log generation
    for host in util.Mock.HOSTS:
        t = OSLogGenerator(host)
        OS_METRIC_THREADS[host] = t

    # Kick off the usage curve in the morning
    events.spawn_timer(util.seconds_until(constants.Usage.KICKOFF_TIME), OAuthTransactionGenerator.usage_curve)

    for host, t in OS_METRIC_THREADS.items():
        events.spawn_timer(3600 * 2, t.disk_cleanup)  # Do disk cleanup every 2 hours

    # TODO: create recurring error events
    events.spawn_timer(3600 * 24, OAuthTransactionGenerator.disk_overflow)

    # TODO: determine error events to simulate (core failure? PF outage? network failure?)
    # need to figure out
    # a) log entries (in PF?) for these failures
    # b) symptoms (KPIs)


# Shutdown callback to gracefully stop running threads
def shutdown(sig, frame):
    print("shutting down")

    events.kill_timers()

    OSLogGenerator.kill_threads()
    OAuthTransactionGenerator.kill_threads()

    for file, logger in LOGGERS.items():
        logger.stop()

    for file, logger in LOGGERS.items():
        logger.join()
        print("Stopped logger for " + file)

    sys.exit(0)

run()
# Listen for a SIGINT or SIGTERM and trigger a shutdown if sent
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
signal.pause()
