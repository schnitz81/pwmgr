import os
import config

# log levels:
# 0 : error
# 1 : info
# 2 : debug

benchmark_running_counter = 0

def log(msg, loglevel):
    # set verbose output from env var if existing, otherwise config file
    verbose_output = None
    if 'VERBOSE_OUTPUT' in os.environ:
        if os.environ['VERBOSE_OUTPUT'].casefold() == 'true' or os.environ['VERBOSE_OUTPUT'] == 1 or os.environ['VERBOSE_OUTPUT'].casefold() == 'yes':
            verbose_output = True
    else:
        try:
            if config.verbose_output.casefold() == 'true' or config.verbose_output == 1 or config.verbose_output.casefold() == 'yes':
                verbose_output = True
        except NameError:
            print("Error: verbose_output needs to be defined as true/false in either config file or as VERBOSE_OUTPUT env variable.")
            exit(1)

    if verbose_output and loglevel > 1:
        print(msg)
    elif loglevel < 2:  # currently no verbosity difference between error and info loglevel
        print(msg)
