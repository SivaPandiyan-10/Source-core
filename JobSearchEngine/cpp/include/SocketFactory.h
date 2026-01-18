#ifndef SOCKET_FACTORY_H
#define SOCKET_FACTORY_H

#include <string>
#include <memory>
#include <atomic>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <functional>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "Ws2_32.lib")
    using socket_t = SOCKET;
    const socket_t INVALID_SOCKET_VAL = INVALID_SOCKET;
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <unistd.h>
    using socket_t = int;
    const socket_t INVALID_SOCKET_VAL = -1;
#endif

#include "message_protocol.h"

using namespace std;

// Exception for network errors
class NetworkException : public std::runtime_error {
public:
    explicit NetworkException(const std::string& a_strErrorMsg) : std::runtime_error(a_strErrorMsg) {}
};

// Handles individual client connections
class TCPClientHandler{
public:
    TCPClientHandler(socket_t a_oClientSocket, 
                  std::function<protocol::Message(const protocol::Message&)> a_fRequestHandler);
    ~TCPClientHandler();

    void Run();
    bool IsConnected() const { return m_abIsConnected; }

private:
    socket_t m_oSocketObj;
    std::atomic<bool> m_abIsConnected;
    std::function<protocol::Message(const protocol::Message&)> m_fRequestHandler;

    // Socket I/O
    bool SendMessage(const protocol::Message& a_pMsg);
    pair<bool, protocol::Message> ReceiveMessage();
    bool SendData(const string& a_strData);
    pair<bool, string> ReceiveData(size_t a_iMaxSize = 65536);
};

// Thread-safe TCP server
class TCPServer {
public:
    TCPServer(const int& a_iPport, 
              std::function<protocol::Message(const protocol::Message&)> request_handler);
    ~TCPServer();

    void StartServer();
    void StopServer();
    bool IsServerRunning() const { return m_abIsServerRunning; }

private:
    int m_iPortNumber;
    socket_t m_oServerSocketObj;
    atomic<bool> m_abIsServerRunning;
    thread m_oThreadObj;
    std::function<protocol::Message(const protocol::Message&)> m_fRequestHandler;

    void InitializeSocket();
    void AcceptConnections();
    void Cleanup();

    static void InitWinSock();
    static void CleanupWinSock();
};


#endif // SOCKET_FACTORY_H
