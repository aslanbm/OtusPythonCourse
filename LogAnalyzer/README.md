# LogAnalyzer 

Примеры запуска: 
	1) python log_analyzer.py  
		В этом случае скрипт найдет, обработает самый новый лог и создаст отчет, отрендерив шаблон report.html.
	2) python log_analyzer.py --config [config_name] 
		Опция --config позволяет подключить внешний конфиг. 
		Можно не указывать имя конфига, так как есть значение по умолчанию: ext_conf.json

В скрипте test_log_analyzer.py реализованы функциональные тесты для анализатора логов.
Запуск: python test_log_analyzer.py 
