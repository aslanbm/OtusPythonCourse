#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip 
import os
import sys
import re
import logging
import itertools
import operator
import json
from datetime import datetime
from collections import namedtuple
from argparse import ArgumentParser

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def find_log(path):
    """Find latest log in path."""
    if not os.path.exists(path):
        raise ValueError('This path doesn\'t exists!')
    
    files = os.listdir(path)
    
    if not files: 
        raise ValueError('This dir is empty!')
    
    pattern = r'nginx-access-ui\.log-(\d+)(\.gz|)'
    regex = re.compile(pattern)
    correct_files = list(filter(regex.search, os.listdir(path)))    

    if not correct_files:
        raise ValueError('There are no correct logs in dir!')
    
    logname = sorted(correct_files)[-1]
    log_search = re.search(pattern, logname)
    dt = datetime.strptime(log_search.group(1), '%Y%m%d')
    LogInfo = namedtuple('LogInfo', 'filename date ext')
    
    return LogInfo(os.path.join(path, logname), dt, log_search.group(2))


def get_url_info(log_row):
    """Parse url and time from log row."""
    try:
        lst = log_row.split('] "')[1].split(' ')
        return lst[1], float(lst[-1])
    except:
        return None, 0


def median(lst):
    """Calculate median of list"""
    if not lst:
        raise ValueError('Empty list')
    
    lst = sorted(lst)
    leng = len(lst)
    idx = leng // 2 
    value = (lst[idx] + lst[idx - 1]) / 2 if leng % 2 == 0 else lst[idx]
    return value


def analyzer(log_info, size):
    """Parse log and create info list."""
    f = gzip.open(log_info.filename, "r") if log_info.ext == '.gz' else open(log_info.filename, 'r')
    data = f.read()
    if not isinstance(data, str):
        data = data.decode("utf-8")
    rows = data.split('\n')[:-1]
    full_info_lst = [get_url_info(log_row) for log_row in rows]
    clean_info_lst = [item for item in full_info_lst if item[0]]
    share = len(clean_info_lst) / len(full_info_lst)

    # Share of success parsed log rows < threshold
    logging.info('Share of success parsed log rows: %.2f' % share)
    if share < 0.5:
        raise ValueError('There are too many bad log rows!')

    info_lst = sorted(clean_info_lst, key=lambda x: x[0])
    
    it = itertools.groupby(info_lst, operator.itemgetter(0))
    cum_cnt, cum_time = 0, 0
    d = {}
    for key, subiter in it:
        lst = [item[1] for item in subiter]
        cnt = len(lst)
        sum_time = sum(lst)
        avg_time = sum_time / cnt
        med_time = median(lst)
        max_time = max(lst)
        cum_cnt += cnt
        cum_time += sum_time
        d[key] = {
            'count': cnt,
            'time_sum': round(sum_time, 3),
            'time_avg': round(avg_time, 3),
            'time_max': round(max_time, 3),
            'time_med': round(med_time, 3)
        }

    for key in d.keys():
        d[key]['count_perc'] = round(100 * d[key]['count'] / cum_cnt, 3)
        d[key]['time_perc'] = round(100 * d[key]['time_sum'] / cum_time, 3)
        d[key]['url'] = key
    
    log_metrics = sorted(list(d.values()), key=lambda x: -x['time_sum'])
    return log_metrics[:size]


def check_report_existance(dt, path):
    """Check report existance."""
    name = 'report-%d.%02d.%02d.html' % (dt.year, dt.month, dt.day)
    return os.path.exists(os.path.join(config['REPORT_DIR'], name))


def create_report(log_report, path, dt):
    """Insert report data to html pattern."""
    with open('report.html', mode='r') as f:
        data = f.read()
    data = data.replace('$table_json', str(log_report))
    name = 'report-%d.%02d.%02d.html' % (dt.year, dt.month, dt.day)
    if not os.path.exists(path):
        os.mkdir(path)
    with open(os.path.join(path, name), mode='w') as f:
        f.write(data)
    

def config_handler(inner_config, config_filename):
    """Handle external config."""    
    if not os.path.exists(config_filename):
        raise ValueError('This config doesn\'t exists!')
    
    with open(config_filename, "r") as conf_file:
        external_config = json.load(conf_file)

    for key in external_config.keys():
        inner_config[key] = external_config[key] 
        
    return inner_config
    

def main(config):
    """Main wrapper."""
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_filename", nargs='?', const="ext_conf.json", help="add path to config file")
    args = parser.parse_args()
    if args.config_filename:
        config = config_handler(config, args.config_filename)

    logging_output = config['LOG_FILE'] if 'LOG_FILE' in config.keys() else None

    logging.basicConfig(filename=logging_output,
                        filemode='w',
                        level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    try:
        log_info = find_log(config['LOG_DIR'])
        logging.info('Log file has been found.')
        if not check_report_existance(log_info.date, config['REPORT_DIR']):
            logging.info('Report doesn\'t exist. So let\'s make it!')
            logging.info('Parsing log file...')
            log_report = analyzer(log_info, config['REPORT_SIZE'])
            logging.info('Log file has been parsed.')
            logging.info('Rendering report...')
            create_report(log_report, config['REPORT_DIR'], log_info.date)
            logging.info('Report has been made.')
        else: 
            logging.info('Report for this log exists.')
    except Exception as ex: 
        logging.exception(ex)


if __name__ == "__main__":
    main(config)
