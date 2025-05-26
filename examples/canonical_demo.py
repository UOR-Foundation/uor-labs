from uor.addressing import DHT

# Simulate storing and retrieving a VM program
PROGRAM = b"PUSH 1\nPUSH 2\nADD\nPRINT"

dht = DHT()

addr = dht.store("org.uor.stdlib.math", PROGRAM)
print("Stored program at", addr)

retrieved = dht.retrieve(addr)
print("Retrieved:\n", retrieved.decode())
