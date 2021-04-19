"""
TCP Socket Speed Test for ESP32 / ESP8266
The counterpart software has to be installed on the ESP target.
Using this script, the usable data-thoughput from the ESP to the computer can be measured.
Depending on network speeds (and ESP clock speed) this test may take a couple of minutes. 
"""
import socket               
import datetime
from time import sleep

"""
CONFIGURATION
"""
# ESP IP in local network
host = "192.168.100.39"

# Regarding ESP32, 5 concurrent streams is the MAXIMUM!
# Regarding ESP8266, no limit of streams is known (testet and could handle easily 100+ streams)
concurrent_connections = 5

"""
PROGRAM
"""
base_port = 80
management_port = 1000

def singleTest():
    print('Single connection test started')
    sock = socket.socket()
    sock.connect((host, base_port))
    data = b''     
    runs = 0
    while runs < 1000:
        byte_counter = 0
        start = datetime.datetime.now()
        while byte_counter < 1024000:
            data = sock.recv(32768)
            byte_counter += len(data)
        
        end = datetime.datetime.now()
        time_per_mb = (end-start).total_seconds()
        speed_mbit = ((2000*512*8)/time_per_mb)/1000000
        time_for_40gb = ((time_per_mb*40000)/60)/60
        print('Time for 1 MB: {time} s \t\tCurrent speed: {speed} Mbit/s\t\tTheoretical time for 40 GB: {time_40gb} h'.format(time=time_per_mb, speed=speed_mbit, time_40gb=time_for_40gb))
        runs += 1
    sock.close()

def setConnectionSettings(connectionsCount):
    print('Setting number of connections in client device')
    sock = socket.socket()
    sock.connect((host, management_port))
    sleep(1)
    sock.send(connectionsCount.to_bytes(1, 'big'))
    sleep(1)
    sock.close()

def parallelTest(connectionsCount):
    setConnectionSettings(connectionsCount)
    sleep(1.0)
    print('Parallel connection test started')
    print('Downloading {connections} chunks of 1 MB at a time. This may take a while! To stop this, press ctrl+C'.format(connections=connectionsCount))
    connections = []
    data_buffers = []
    byte_counts = []
    for i in range(connectionsCount):
        sock = socket.socket()
        sock.connect((host, base_port + i))
        connections.append(sock)
        data_buffers.append(b'')
        byte_counts.append(0)
    
    runs = 0
    host_is_alive = False
    while runs < 1000:
        start = datetime.datetime.now()
        for index, byte_count in enumerate(byte_counts):
            byte_counts[index] = 0

        while all(x < 1024000 for x in byte_counts):
            # print(byte_counts)
            if host_is_alive == False:
                if(all(x > 0 for x in byte_counts)):
                    host_is_alive = True
                    print("[SUCCESS] Host is alive and all streams are carrying data. Please wait for test to finish...")
                else:
                    if (datetime.datetime.now() - start).total_seconds() > 2:
                        print("[ERROR] Host does not seem to send anything")
                        return
            for index, (buffer, sock, byte_count) in enumerate(zip(data_buffers, connections, byte_counts)):
                data_buffers[index] = connections[index].recv(32768)
                byte_counts[index] += len(data_buffers[index])
                # print('Connection no.: {num}, byte count: {count}'.format(num = index, count = byte_counts[index]))
    
        end = datetime.datetime.now()
        time_per_mb = ((end-start).total_seconds()) / connectionsCount
        speed_mbit = ((2000*512*8)/time_per_mb)/1000000
        time_for_40gb = ((time_per_mb*40000)/60)/60
        print('[TEST RESULT WITH {connections} ACTIVE STREAMS] \t\tTime for 1 MB: {time:.4f} s \t\tCurrent speed: {speed:.4f} Mbit/s\t\tTheoretical time for 40 GB: {time_40gb:.4f} h'.format(connections=connectionsCount, time=time_per_mb, speed=speed_mbit, time_40gb=time_for_40gb))
        runs += 1
    for sock in connections:
        sock.close()

if __name__ == '__main__':
    # singleTest()
    parallelTest(concurrent_connections)