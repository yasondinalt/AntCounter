# AntCounter
Python3, OpenCV3 port of https://sites.google.com/site/antcounter/

1. I don't know how properly fix code in lines 143-145: "def ants_account" so I just add "try: except:" block. Bug create false-positives on video begining.

2. Because of restrictions of Tkinter (new windows can be created only from main thread), after AppAntCounter end of excecution I pass object to main thread to show MathPlot statistics. Line 74 "def graph"
