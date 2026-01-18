#include "SocketFactory.h"
#include <iostream>
#include <sstream>
#include <memory>
#include <vector>

#ifdef _WIN32
    #include <winsock2.h>
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <fcntl.h>
    #define closesocket close
#endif

// TCPClientHandler implementation
TCPClientHandler::TCPClientHandler(socket_t a_oClient_socket, 
                             std::function<protocol::Message(const protocol::Message&)> a_fRequestHandler)
    : m_oSocketObj(a_oClient_socket), m_abIsConnected(true), m_fRequestHandler(a_fRequestHandler) {}

TCPClientHandler::~TCPClientHandler() {
    if (m_oSocketObj != INVALID_SOCKET_VAL) {
        closesocket(m_oSocketObj);
    }
}

bool TCPClientHandler::SendData(const std::string& a_strData) {
    if (m_oSocketObj == INVALID_SOCKET_VAL || !m_abIsConnected) {
        return false;
    }
    
    int l_iTotalDataSent = 0;
    int l_iDataLen = static_cast<int>(a_strData.length());

    while (l_iTotalDataSent < l_iDataLen) {
        int l_iSent = send(m_oSocketObj, a_strData.c_str() + l_iTotalDataSent, l_iDataLen - l_iTotalDataSent, 0);
        if (l_iSent == -1) {
            m_abIsConnected = false;
            return false;
        }
        l_iTotalDataSent += l_iSent;
    }
    
    return true;
}

std::pair<bool, std::string> TCPClientHandler::ReceiveData(size_t a_iMaxSize) {
    if (m_oSocketObj == INVALID_SOCKET_VAL || !m_abIsConnected) {
        return {false, ""};
    }
    
    std::vector<char> l_vBuffer(a_iMaxSize);
    int l_iReceived = recv(m_oSocketObj, l_vBuffer.data(), static_cast<int>(a_iMaxSize - 1), 0);

    if (l_iReceived <= 0) {
        m_abIsConnected = false;
        return {false, ""};
    }

    return {true, std::string(l_vBuffer.data(), l_iReceived)};
}

bool TCPClientHandler::SendMessage(const protocol::Message& a_strMsg) {
    std::string l_strFramed = a_strMsg.frame();
    return SendData(l_strFramed);
}

std::pair<bool, protocol::Message> TCPClientHandler::ReceiveMessage() {
    auto [l_bIsSuccess, l_pData] = ReceiveData(65536);
    if (!l_bIsSuccess) {
        return std::make_pair(false, protocol::Message());
    }

    return protocol::Message::parse_framed(l_pData);
}

void TCPClientHandler::Run() {
    std::cout << "[TCPClientHandler] Client connected" << std::endl;
    
    while (m_abIsConnected) {
        auto [l_bIsSuccess, l_pRequest] = ReceiveMessage();
        
        if (!l_bIsSuccess) {
            std::cerr << "[TCPClientHandler] Failed to receive message" << std::endl;
            break;
        }
        
        std::cout << "[TCPClientHandler] Received request type: " 
                  << protocol::Message::message_type_to_string(l_pRequest.type) << std::endl;
        
        // Process request
        protocol::Message l_pResponse = m_fRequestHandler(l_pRequest);
        
        // Send response
        if (!SendMessage(l_pResponse)) {
            std::cerr << "[TCPClientHandler] Failed to send response" << std::endl;
            break;
        }
        
        // Check for shutdown
        if (l_pRequest.type == protocol::MessageType::SHUTDOWN) {
            std::cout << "[TCPClientHandler] Shutdown request received" << std::endl;
            break;
        }
    }
    
    std::cout << "[TCPClientHandler] Client disconnected" << std::endl;
}

// TCPServer implementation
TCPServer::TCPServer(const int& a_iPortNumber, 
                     std::function<protocol::Message(const protocol::Message&)> a_fRequestHandler)
    : m_iPortNumber(a_iPortNumber),
     m_oServerSocketObj(INVALID_SOCKET_VAL),
     m_abIsServerRunning(false), 
     m_fRequestHandler(a_fRequestHandler) 
     {
#ifdef _WIN32
    InitWinSock();
#endif
}

TCPServer::~TCPServer() 
{
    StopServer();
#ifdef _WIN32
    CleanupWinSock();
#endif
}

void TCPServer::InitWinSock() 
{
#ifdef _WIN32
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        throw NetworkException("WSAStartup failed");
    }
#endif
}

void TCPServer::CleanupWinSock() 
{
#ifdef _WIN32
    WSACleanup();
#endif
}

void TCPServer::InitializeSocket() {
    m_oServerSocketObj = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (m_oServerSocketObj == INVALID_SOCKET_VAL) {
        throw NetworkException("Failed to create socket");
    }
    
    // Set SO_REUSEADDR to allow reusing the port
    int l_iReuse = 1;
    if (setsockopt(m_oServerSocketObj, SOL_SOCKET, SO_REUSEADDR, 
                   reinterpret_cast<const char*>(&l_iReuse), sizeof(l_iReuse)) < 0) {
        throw NetworkException("setsockopt failed");
    }
    
    // Bind socket
    struct sockaddr_in l_sServerAddr;
    l_sServerAddr.sin_family = AF_INET;
    l_sServerAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    l_sServerAddr.sin_port = htons(m_iPortNumber);
    
    if (bind(m_oServerSocketObj, (struct sockaddr*)&l_sServerAddr, sizeof(l_sServerAddr)) < 0) {
        throw NetworkException("Bind failed");
    }
    
    // Listen
    if (listen(m_oServerSocketObj, SOMAXCONN) < 0) {
        throw NetworkException("Listen failed");
    }
    
    std::cout << "[TCPServer] Listening on port " << m_iPortNumber << std::endl;
}

void TCPServer::AcceptConnections() {
    std::cout << "[TCPServer] Accept thread started" << std::endl;
    
    while (m_abIsServerRunning) {
        struct sockaddr_in l_sClientAddr;
        int l_iClientAddrLen = sizeof(l_sClientAddr);
        
        socket_t l_oClientSocketObj = accept(m_oServerSocketObj, 
                                       (struct sockaddr*)&l_sClientAddr, 
                                       &l_iClientAddrLen);
        
        if (l_oClientSocketObj == INVALID_SOCKET_VAL) {
            if (m_abIsServerRunning) {
                std::cerr << "[TCPServer] Accept failed" << std::endl;
            }
            break;
        }
        
        // Handle client in a new thread
        auto handler = std::make_shared<TCPClientHandler>(l_oClientSocketObj, m_fRequestHandler);
        std::thread client_thread([handler]() {
            handler->Run();
        });
        client_thread.detach(); // Let thread run independently
    }
    
    std::cout << "[TCPServer] Accept thread exiting" << std::endl;
}

void TCPServer::StartServer() {
    if (m_abIsServerRunning) {
        return;
    }
    
    try {
        InitializeSocket();
        m_abIsServerRunning = true;
        m_oThreadObj = std::thread(&TCPServer::AcceptConnections, this);
    } catch (const NetworkException& e) {
        std::cerr << "[TCPServer] Error: " << e.what() << std::endl;
        throw;
    }
}

void TCPServer::StopServer() {
    if (!m_abIsServerRunning) 
    {
        return;
    }
    m_abIsServerRunning = false;
    if (m_oServerSocketObj != INVALID_SOCKET_VAL)
    {
        closesocket(m_oServerSocketObj);
        m_oServerSocketObj = INVALID_SOCKET_VAL;
    }
    if (m_oThreadObj.joinable()) 
    {
        m_oThreadObj.join();
    }
    std::cout << "[TCPServer] Server stopped" << std::endl;
}

