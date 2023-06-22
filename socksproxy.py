import paramiko
import socket
import socks

# Configure the SSH connection details
ssh_host = 'AWS_SERVER_IP'
ssh_port = 22
ssh_username = 'USERNAME'
ssh_password = 'PASSWORD'
local_proxy_port = 1080

# Configure the web browser proxy settings
browser_proxy_host = 'localhost'
browser_proxy_port = local_proxy_port

def create_ssh_tunnel():
    # Create a socket to act as the local SOCKS5 proxy
    local_proxy_socket = socks.socksocket()
    local_proxy_socket.set_proxy(socks.SOCKS5, browser_proxy_host, browser_proxy_port)

    # Connect the local proxy socket to the AWS server
    local_proxy_socket.connect((ssh_host, ssh_port))

    # Create an SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the AWS server using SSH
    ssh_client.connect(ssh_host, ssh_port, ssh_username, ssh_password)

    # Create a transport over the SSH connection
    transport = ssh_client.get_transport()

    # Create a dynamic port forward (SOCKS5 proxy) over the SSH transport
    local_port = transport.request_port_forward('', local_proxy_port)
    
    print(f'Successfully established a tunnel. Proxy is listening on {browser_proxy_host}:{browser_proxy_port}')
    
    try:
        # Start listening on the local proxy socket
        while True:
            # Accept incoming connections from the web browser
            browser_socket, addr = local_proxy_socket.accept()
            print(f'Accepted connection from {addr[0]}')

            # Connect to the target host through the SSH tunnel
            target_socket = transport.open_channel('direct-tcpip', ('localhost', 22), addr)

            if target_socket is not None:
                # Forward data between the web browser and the target host
                forward_data(browser_socket, target_socket)
    except KeyboardInterrupt:
        print('SSH tunneling terminated.')
    except Exception as e:
        print(f'Error occurred during tunneling: {str(e)}')

    # Close the SSH client connection
    ssh_client.close()

def forward_data(src_socket, dest_socket):
    while True:
        # Read data from the source socket (web browser)
        data = src_socket.recv(4096)

        if len(data) == 0:
            break

        # Send the data to the destination socket (target host)
        dest_socket.sendall(data)

    # Close both sockets
    src_socket.close()
    dest_socket.close()

# Start the SSH tunnel
create_ssh_tunnel()
