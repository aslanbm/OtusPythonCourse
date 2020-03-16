#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from log_analyzer import * 


class TestLogAnalyzer(unittest.TestCase):
    def test_get_url_info(self):
        self.assertEqual(get_url_info('1.194.135.240 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2/sites/?date_to=2017-06-28 HTTP/1.1" 200 22 "-" "python-requests/2.13.0" "-" "1498697423-3979856266-4708-9752782" "8a7741a54297568b" 0.061'), ('/api/v2/sites/?date_to=2017-06-28', 0.061))

    def test_median(self):
        self.assertEqual(median([1, 2, 3, 4, 5]), 3)
        self.assertEqual(median([10, 50, 30, 20]), 25)

    def test_find_log(self):
        # create temp file in path
        path = 'test_path'
        os.mkdir(path)
        pattern = 'nginx-access-ui.log-201806%02d'
        fnames = [os.path.join(path, pattern % i) for i in range(21)]
        for fname in fnames:
            with open(fname, 'a') as f:
                pass 

        LogInfo = namedtuple('LogInfo', 'filename date ext')
        dt = datetime.strptime('20180620', '%Y%m%d')
        res = LogInfo(fnames[-1], dt, '')
        cur_res = find_log(path)
        for fname in fnames: 
            os.remove(fname)
        os.rmdir(path)
        self.assertEqual(cur_res, res)

    def test_config_handler(self):
        inner_conf = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log"
        }
        ext_conf = {
            "REPORT_SIZE": 1250,
            "REPORT_DIR": "./new_reports",
            "LOG_FILE": "./logfile.log"
        }
        path, conf_name = 'test_path', 'ext_conf.json'
        os.mkdir(path)
        with open(os.path.join(path, conf_name), "w") as f:
            json.dump(ext_conf, f) 

        res = {
            "REPORT_SIZE": 1250,
            "REPORT_DIR": "./new_reports",
            "LOG_DIR": "./log",
            "LOG_FILE": "./logfile.log"
        }
        cur_res = config_handler(inner_conf, os.path.join(path, conf_name))
        os.remove(os.path.join(path, conf_name))
        os.rmdir(path)
        self.assertEqual(cur_res, res)

if __name__ == "__main__":
    unittest.main()