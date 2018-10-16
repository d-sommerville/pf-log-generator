OS_METRIC_GENERATION_INTERVAL = 60
BASE_LOG_DIR = '/var/log/mock/'


class OAuth:
    TXN_MIN_THREADS = 15
    TXN_MAX_THREADS = 20
    TXN_CACHE_TTL = 300
    MIN_AUTHN_TIME = 5
    MAX_AUTHN_TIME = 10
    MIN_REFRESH_TIME = 10
    MAX_REFRESH_TIME = 15
    AUTH_CODE_LIFETIME = 15
    ACCESS_TOKEN_LIFETIME = 60
    REFRESH_TOKEN_LIFETIME = 120


# TODO: ps and network logs (what do we need from these?)
class Logs:
    AUDIT_LOG = BASE_LOG_DIR + 'audit.log'
    CPU_USAGE_LOG = BASE_LOG_DIR + 'cpu.log'
    DISK_USAGE_LOG = BASE_LOG_DIR + 'df.log'
    MEMORY_USAGE_LOG = BASE_LOG_DIR + 'mem.log'


class Events:
    AUTHENTICATION_ATTEMPT = 'AUTHN_ATTEMPT'
    OAUTH = 'OAuth'


class Roles:
    IDP = 'IdP'
    AS = 'AS'


class Clients:
    RS_CLIENT = 'rs_client'


class Protocols:
    OAUTH2 = 'OAuth20'


class GrantTypes:
    AUTH_CODE = 'authorization_code'
    VALIDATE_BEARER = 'urn:pingidentity.com:oauth2:grant_type:validate_bearer'
    REFRESH = 'refresh_token'


class Statuses:
    SUCCESS = 'success'
    IN_PROGRESS = 'inprogress'
    FAILURE = 'failure'


class Errors:
    INVALID_CLIENT_ID = 'Unknown or invalid client_id'
    AUTHZ_CODE_EXPIRED = 'invalid_grant: Authorization code is invalid or expired.'
    INVALID_SECRET = 'invalid_client: Invalid client or client credentials'
    INVALID_SCOPE = 'invalid_scope: The requested scope(s) must be blank or a subset of the provided scopes.'
    INVALID_REFRESH_TOKEN = 'invalid_grant: unknown, invalid, or expired refresh token'
    TOKEN_EXPIRED = 'invalid_grant: token expired'


class Usage:
    KICKOFF_TIME = 6  # Kick off the usage curve hike at 6am
    PEAK_TIME = 11  # Peak at 11am
    DROPOFF_TIME = 20  # Drop off usage at 8pm
    INCREASE_INTERVAL = 5  # Increase usage every 5 minutes
    INCREASE_VOLUME = 5  # Number of threads to spawn every interval


class Cpu:
    MIN_BASE_USAGE = 5
    MAX_BASE_USAGE = 10
    MAX_USAGE_PER_TRANSACTION = 0.25
    ALL = 'all'
    DEFAULT_NICE = 0
    DEFAULT_SYS = 0
    DEFAULT_WAIT = 0
    NICE_MAX = 5
    SYS_MAX = 20
    WAIT_MAX = 15


class Memory:
    MIN_BASE_USAGE = 1000
    MAX_BASE_USAGE = 2500
    MIN_PROCESSES = 100
    MAX_PROCESSES = 150
    MIN_THREADS = 300
    MAX_THREADS = 400
    MIN_INTERRUPTS = 500
    MAX_INTERRUPTS = 750
    MAX_USAGE_PER_TRANSACTION = 100
    DEFAULT_TOTAL = 32 * 1024  # 32GB in MB


class Disk:
    MIN_BASE_USAGE = 5
    MAX_BASE_USAGE = 25
    USAGE_INCREMENT_PER_TRANSACTION = 0.01
    FILESYSTEM_DEFAULT = 'none'
    DISK_SIZE_DEFAULT = 100
    MOUNT_PATH_DEFAULT = '/'
