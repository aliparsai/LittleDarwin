find ~/Study/LittleDarwin/Cases/FirstOrder/ -iname report.txt -exec python ~/Study/LittleDarwin/HigherOrderExperiment/ReportParser.py {} ~/Study/LittleDarwin/HigherOrderExperiment/analyze/fo.csv 120 \;
find ~/Study/LittleDarwin/Cases/SecondOrder/ -iname report.txt -exec python ~/Study/LittleDarwin/HigherOrderExperiment/ReportParser.py {} ~/Study/LittleDarwin/HigherOrderExperiment/analyze/so.csv 60 \;
find ~/Study/LittleDarwin/Cases/ThirdOrder/ -iname report.txt -exec python ~/Study/LittleDarwin/HigherOrderExperiment/ReportParser.py {} ~/Study/LittleDarwin/HigherOrderExperiment/analyze/to.csv 40 \;

