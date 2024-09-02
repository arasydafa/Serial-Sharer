import serial
import threading
import time


class SerialSharer:
    def __init__(self, slave_port, master_ports):
        # Initialize Serial objects for slave port and master ports
        self.slave_port = serial.Serial(slave_port, 57600, timeout=1)
        self.slave_port.set_buffer_size(rx_size=12800, tx_size=12800)
        self.master_ports = [serial.Serial(
            port, 57600, timeout=1) for port in master_ports]
        for port in self.master_ports:
            port.set_buffer_size(rx_size=12800, tx_size=12800)
        # Create a lock to ensure thread safety
        self.lock = threading.Lock()
        # Initialize the current master port as None
        self.current_master = None

    def handle_master(self, master_port):
        while True:
            # Acquire the lock to ensure exclusive access to current_master
            self.lock.acquire()
            # If there's no current master or the current master is the same as this master port
            if self.current_master is None or self.current_master == master_port:
                # Set the current master to this master port
                self.current_master = master_port
                # Release the lock after updating current_master
                self.lock.release()
                # Read request from the master port
                request = master_port.readline().decode().strip()
                if request:
                    # Print received request from the master port
                    print(
                        f"Received request from {master_port.name}: {request}")
                    # Write the request to the slave port
                    self.slave_port.write(request.encode())
                    # Read response from the slave port
                    response = self.slave_port.readline().decode().strip()
                    # Print the response being sent to the master port
                    print(
                        f"Sending response to {master_port.name}: {response}")
                    # Write the response to the master port
                    master_port.write(response.encode())
            else:
                # Release the lock if this master port is not the current master
                self.lock.release()
                # If this master port is not the current master, sleep briefly
                time.sleep(0.1)

    def start(self):
        threads = []
        # Start a thread for each master port
        for master_port in self.master_ports:
            thread = threading.Thread(
                target=self.handle_master, args=(master_port,))
            thread.start()
            threads.append(thread)
        # Wait for all threads to finish
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    # Setup slave port and master ports
    slave_port_name = "COM1"
    master_ports_names = ["COM5", "COM3"]

    # Create a SerialSharer instance and start sharing
    sharer = SerialSharer(slave_port_name, master_ports_names)
    try:
        sharer.start()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close serial ports
        sharer.slave_port.close()
        for port in sharer.master_ports:
            port.close()
