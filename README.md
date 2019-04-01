#TCP Congestion Control
## Javier Palomares
Python code to measure tcp congestion control using mininet and iperf. 
The code executes iperf for 100 seconds for 4 different tcp control algorithms across
the dumbbell topology at different delays.

### To execute
Note: Must be executed using python 2.7. Mininet must be installed, and it's suggested to run on a VM 
following the instructions at http://mininet.org/download/

* To generate data:
`python dumbbell_topo.py`
* To plot data:
`python plot.py`

