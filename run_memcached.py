#!/usr/bin/env python3

import paramiko
import os
from time import sleep
from util import *
from config_remote import *

################################
### Experiemnt Configuration ###
################################

# Server overload algorithm (breakwater, seda, dagor, nocontrol)
OVERLOAD_ALG = "breakwater"

# The number of client connections
NUM_CONNS = 1000

# List of offered load
OFFERED_LOADS = [500000, 1000000, 1500000, 2000000, 2500000, 3000000,
                 3500000, 4000000, 4500000, 5000000, 5500000, 6000000]

MAX_KEY_INDEX = 100000

ENABLE_DIRECTPATH = True
SPIN_SERVER = True
DISABLE_WATCHDOG = False

NUM_CORES_SERVER = 10
NUM_CORES_CLIENT = 16

slo = 50
POPULATING_LOAD = 200000

############################
### End of configuration ###
############################

# Verify configs #
if OVERLOAD_ALG not in ["breakwater", "seda", "dagor", "nocontrol"]:
    print("Unknown overload algorithm: " + OVERLOAD_ALG)
    exit()

cmd = "sed -i'.orig' -e \'s/#define SBW_RTT_US.*/#define SBW_RTT_US\\t\\t\\t{:d}/g\'"\
        " configs/bw_config.h".format(NET_RTT)
execute_local(cmd)

### Function definitions ###
def generate_shenango_config(is_server ,conn, ip, netmask, gateway, num_cores,
        directpath, spin, disable_watchdog):
    config_name = ""
    config_string = ""
    if is_server:
        config_name = "server.config"
        config_string = "host_addr {}".format(ip)\
                      + "\nhost_netmask {}".format(netmask)\
                      + "\nhost_gateway {}".format(gateway)\
                      + "\nruntime_kthreads {:d}".format(num_cores)
    else:
        config_name = "client.config"
        config_string = "host_addr {}".format(ip)\
                      + "\nhost_netmask {}".format(netmask)\
                      + "\nhost_gateway {}".format(gateway)\
                      + "\nruntime_kthreads {:d}".format(num_cores)

    if spin:
        config_string += "\nruntime_spinning_kthreads {:d}".format(num_cores)

    if directpath:
        config_string += "\nenable_directpath 1"

    if disable_watchdog:
        config_string += "\ndisable_watchdog 1"

    cmd = "cd ~/{} && echo \"{}\" > {} "\
            .format(ARTIFACT_PATH,config_string, config_name)

    return execute_remote([conn], cmd, True)
### End of function definition ###

NUM_AGENT = len(AGENTS)

# configure Shenango IPs for config
server_ip = "192.168.1.200"
client_ip = "192.168.1.100"
agent_ips = []
netmask = "255.255.255.0"
gateway = "192.168.1.1"

for i in range(NUM_AGENT):
    agent_ip = "192.168.1." + str(101 + i);
    agent_ips.append(agent_ip)

k = paramiko.RSAKey.from_private_key_file(KEY_LOCATION)
# connection to server
server_conn = paramiko.SSHClient()
server_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
server_conn.connect(hostname = SERVER, username = USERNAME, pkey = k)

# connection to client
client_conn = paramiko.SSHClient()
client_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client_conn.connect(hostname = CLIENT, username = USERNAME, pkey = k)

# connections to agents
agent_conns = []
for agent in AGENTS:
    agent_conn = paramiko.SSHClient()
    agent_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    agent_conn.connect(hostname = agent, username = USERNAME, pkey = k)
    agent_conns.append(agent_conn)

# Clean-up environment
print("Cleaning up machines...")
cmd = "sudo killall -9 memcached & sudo killall -9 iokerneld"
execute_remote([server_conn], cmd, True, False)

cmd = "sudo killall -9 mcclient & sudo killall -9 iokerneld"
execute_remote([client_conn] + agent_conns,
               cmd, True, False)
sleep(1)


# Distribuing config files
print("Distributing configs...")
# - server
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*"\
        " {}@{}:~/{}/shenango/breakwater/src/ >/dev/null"\
        .format(KEY_LOCATION, USERNAME, SERVER, ARTIFACT_PATH)
execute_local(cmd)
# - client
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*"\
        " {}@{}:~/{}/shenango/breakwater/src/ >/dev/null"\
        .format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH)
execute_local(cmd)
# - agents
for agent in AGENTS:
    cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no configs/*"\
            " {}@{}:~/{}/shenango/breakwater/src/ >/dev/null"\
            .format(KEY_LOCATION, USERNAME, agent, ARTIFACT_PATH)
    execute_local(cmd)

# Generating config files
print("Generating config files...")
generate_shenango_config(True, server_conn, server_ip, netmask, gateway,
                         NUM_CORES_SERVER, ENABLE_DIRECTPATH, SPIN_SERVER, DISABLE_WATCHDOG)
generate_shenango_config(False, client_conn, client_ip, netmask, gateway,
                         NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)
for i in range(NUM_AGENT):
    generate_shenango_config(False, agent_conns[i], agent_ips[i], netmask,
                             gateway, NUM_CORES_CLIENT, ENABLE_DIRECTPATH, True, False)

# Rebuild Shanango
print("Building Shenango...")
cmd = "cd ~/{}/shenango && make clean && make && make -C bindings/cc"\
        .format(ARTIFACT_PATH)
execute_remote([server_conn, client_conn] + agent_conns,
               cmd, True)

# Build Breakwater
print("Building Breakwater...")
cmd = "cd ~/{}/shenango/breakwater && make clean && make && make -C bindings/cc"\
        .format(ARTIFACT_PATH)
execute_remote([server_conn, client_conn] + agent_conns,
                 cmd, True)

# Build Memcached
print("Building memcached...")
cmd = "cd ~/{}/shenango-memcached && make clean && make"\
        .format(ARTIFACT_PATH)
execute_remote([server_conn], cmd, True)

# Build McClient
print("Building mcclient...")
cmd = "cd ~/{}/memcached-client && make clean && make"\
        .format(ARTIFACT_PATH)
execute_remote([client_conn] + agent_conns, cmd, True)

# Execute IOKernel
iok_sessions = []
print("Executing IOKernel...")
cmd = "cd ~/{}/shenango && sudo ./iokerneld".format(ARTIFACT_PATH)
iok_sessions += execute_remote([server_conn, client_conn] + agent_conns,
                               cmd, False)

sleep(1)

# Start memcached
print("Starting Memcached server...")
cmd = "cd ~/{} && sudo ./shenango-memcached/memcached {} server.config"\
        " -p 8001 -v -c 32768 -m 64000 -b 32768 -o hashpower=18"\
        .format(ARTIFACT_PATH, OVERLOAD_ALG)
server_session = execute_remote([server_conn], cmd, False)
server_session = server_session[0]

sleep(2)
print("Populating entries...")
cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config client {:d} {} SET"\
        " {:d} {:d} {:d} {:d} >stdout.out 2>&1"\
        .format(ARTIFACT_PATH, OVERLOAD_ALG, NUM_CONNS, server_ip, MAX_KEY_INDEX,
                slo, 0, POPULATING_LOAD)
client_session = execute_remote([client_conn], cmd, False)
client_session = client_session[0]

client_session.recv_exit_status()

sleep(1)

# Remove temporary output
cmd = "cd ~/{} && rm output.csv output.json".format(ARTIFACT_PATH)
execute_remote([client_conn], cmd, True, False)

sleep(1)

for offered_load in OFFERED_LOADS:
    print("Load = {:d}".format(offered_load))
    # - clients
    print("\tExecuting client...")
    client_agent_sessions = []
    cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config client {:d} {}"\
            " USR {:d} {:d} {:d} {:d} >stdout.out 2>&1"\
            .format(ARTIFACT_PATH, OVERLOAD_ALG, NUM_CONNS, server_ip,
                    MAX_KEY_INDEX, slo, NUM_AGENT, offered_load)
    client_agent_sessions += execute_remote([client_conn], cmd, False)

    sleep(1)

    # - Agents
    print("\tExecuting agents...")
    cmd = "cd ~/{} && sudo ./memcached-client/mcclient {} client.config agent {}"\
            " >stdout.out 2>&1".format(ARTIFACT_PATH, OVERLOAD_ALG, client_ip)
    client_agent_sessions += execute_remote(agent_conns, cmd, False)

    # Wait for client and agents
    print("\tWaiting for client and agents...")
    for client_agent_session in client_agent_sessions:
        client_agent_session.recv_exit_status()

    sleep(2)


# Kill server
cmd = "sudo killall -9 memcached"
execute_remote([server_conn], cmd, True)

# Wait for the server
server_session.recv_exit_status()

# Kill IOKernel
cmd = "sudo killall -9 iokerneld"
execute_remote([server_conn, client_conn] + agent_conns, cmd, True)

# Wait for IOKernel sessions
for iok_session in iok_sessions:
    iok_session.recv_exit_status()

# Close connections
server_conn.close()
client_conn.close()
for agent_conn in agent_conns:
    agent_conn.close()

# Create output directory
if not os.path.exists("outputs"):
    os.mkdir("outputs")

# Move output.csv and output.json
print("Collecting outputs...")
cmd = "scp -P 22 -i {} -o StrictHostKeyChecking=no {}@{}:~/{}/output.csv ./"\
        " >/dev/null".format(KEY_LOCATION, USERNAME, CLIENT, ARTIFACT_PATH)
execute_local(cmd)

output_prefix = "{}".format(OVERLOAD_ALG)

if SPIN_SERVER:
    output_prefix += "_spin"

if DISABLE_WATCHDOG:
    output_prefix += "_nowd"

output_prefix += "_memcached_nconn_{:d}".format(NUM_CONNS)

# Print Headers
header = "num_clients,offered_load,throughput,goodput,cpu,min,mean,p50,p90,p99,p999,p9999"\
        ",max,lmin,lmean,lp50,lp90,lp99,lp999,lp9999,lmax,p1_win,mean_win,p99_win,p1_q,mean_q,p99_q,server:rx_pps"\
        ",server:tx_pps,server:rx_bps,server:tx_bps,server:rx_drops_pps,server:rx_ooo_pps"\
        ",server:winu_rx_pps,server:winu_tx_pps,server:win_tx_wps,server:req_rx_pps"\
        ",server:resp_tx_pps,client:min_tput,client:max_tput"\
        ",client:winu_rx_pps,client:winu_tx_pps,client:resp_rx_pps,client:req_tx_pps"\
        ",client:win_expired_wps,client:req_dropped_rps"
cmd = "echo \"{}\" > outputs/{}.csv".format(header, output_prefix)
execute_local(cmd)

cmd = "cat output.csv >> outputs/{}.csv".format(output_prefix)
execute_local(cmd)

# Remove temp outputs
cmd = "rm output.csv"
execute_local(cmd, False)

print("Output generated: outputs/{}.csv".format(output_prefix))
print("Done.")
