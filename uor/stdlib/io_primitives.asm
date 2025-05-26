# IO VM primitive implementations

# Console input
io_read:
    INPUT
    RET

# Console output  
io_print:
    LOAD 0  # parameter
    PRINT
    RET

# File operations using SYSCALL
file_open:
    PUSH 1  # open syscall
    LOAD 0  # filename address
    SYSCALL
    RET

file_read:
    PUSH 2  # read syscall
    LOAD 0  # handle
    LOAD 1  # size
    SYSCALL
    RET

file_write:
    PUSH 3  # write syscall
    LOAD 0  # handle
    LOAD 1  # data address
    LOAD 2  # size
    SYSCALL
    RET

file_close:
    PUSH 4  # close syscall
    LOAD 0  # handle
    SYSCALL
    RET

# Network primitives
net_connect:
    PUSH 10  # connect syscall
    LOAD 0   # address
    LOAD 1   # port
    SYSCALL
    RET

net_send:
    NET_SEND
    RET

net_recv:
    NET_RECV
    RET

# IPFS integration
ipfs_add:
    PUSH 20  # IPFS add syscall
    LOAD 0   # data address
    LOAD 1   # size
    SYSCALL
    RET

ipfs_get:
    PUSH 21  # IPFS get syscall
    LOAD 0   # CID address
    SYSCALL
    RET
