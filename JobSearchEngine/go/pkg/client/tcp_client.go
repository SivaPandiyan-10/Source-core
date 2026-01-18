package client

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"time"
)

// ===== DATA STRUCTURES =====

// Message - A single TCP message sent over the network
type Message struct {
	Type    string          `json:"type"`              // Message type (e.g., "PING", "REQUEST")
	Payload json.RawMessage `json:"payload,omitempty"` // The actual data
}

// ===== TCP CLIENT =====

// TCPClient - Handles the connection to the C++ server
type TCPClient struct {
	address              string        // Server address like "localhost:10000"
	conn                 net.Conn      // The actual network connection
	timeout              time.Duration // How long to wait before timing out
	reconnectDelay       time.Duration // Wait time before retrying connection
	maxReconnectAttempts int           // Maximum number of reconnection attempts
}

// ===== CONSTRUCTOR =====

// NewTCPClient - Creates a new TCP client
// Parameters:
//
//	address - Server address (e.g., "localhost:10000")
//	timeout - How long to wait for operations (e.g., 10 seconds)
//
// Returns: A new TCP client ready to use
func NewTCPClient(address string, timeout time.Duration) *TCPClient {
	return &TCPClient{
		address:              address,
		timeout:              timeout,
		reconnectDelay:       time.Second, // Start with 1 second
		maxReconnectAttempts: 10,          // Try up to 10 times
	}
}

// ===== CONNECTION MANAGEMENT =====

// Connect - Connects to the server (just one attempt)
// Parameters:
//
//	ctx - Context for cancellation
//
// Returns: Error if connection fails
func (c *TCPClient) Connect(ctx context.Context) error {
	// Create a dialer with timeout
	dialer := net.Dialer{
		Timeout: c.timeout,
	}

	// Try to connect
	conn, err := dialer.DialContext(ctx, "tcp", c.address)
	if err != nil {
		return fmt.Errorf("failed to connect to server at %s: %w", c.address, err)
	}

	// Store the connection
	c.conn = conn
	fmt.Printf("[TCPClient] Connected to %s\n", c.address)
	return nil
}

// ConnectWithRetry - Tries to connect multiple times with increasing delays
// This is useful when the server might not be available immediately
// Parameters:
//
//	ctx - Context for cancellation
//
// Returns: Error if all attempts fail
func (c *TCPClient) ConnectWithRetry(ctx context.Context) error {
	waitTime := time.Second    // Start with 1 second
	maxWaitTime := time.Minute // Don't wait more than 1 minute

	for attempt := 0; attempt < c.maxReconnectAttempts; attempt++ {
		// Check if we should cancel
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		// Try to connect
		if err := c.Connect(ctx); err == nil {
			// Success!
			return nil
		}

		// If we have more attempts left...
		if attempt < c.maxReconnectAttempts-1 {
			fmt.Printf("[TCPClient] Connection failed, retrying in %v (attempt %d/%d)\n",
				waitTime, attempt+1, c.maxReconnectAttempts)

			// Wait before retrying
			select {
			case <-time.After(waitTime):
				// Time to try again
			case <-ctx.Done():
				// We were told to stop
				return ctx.Err()
			}

			// Increase wait time for next attempt (exponential backoff)
			waitTime = waitTime * 2
			if waitTime > maxWaitTime {
				waitTime = maxWaitTime
			}
		}
	}

	return fmt.Errorf("failed to connect after %d attempts", c.maxReconnectAttempts)
}

// ===== SENDING & RECEIVING =====

// SendMessage - Sends a message to the server
// The message is converted to JSON and sent with a length prefix
// Parameters:
//
//	msg - The message to send (will be converted to JSON)
//
// Returns: Error if sending fails
func (c *TCPClient) SendMessage(msg interface{}) error {
	// Check if we're connected
	if c.conn == nil {
		return fmt.Errorf("not connected to server")
	}

	// Convert message to JSON
	jsonData, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("failed to convert message to JSON: %w", err)
	}

	// Create a frame: first 4 bytes are the message length
	frame := make([]byte, 4+len(jsonData))
	binary.BigEndian.PutUint32(frame, uint32(len(jsonData)))
	copy(frame[4:], jsonData)

	// Set a timeout for this write operation
	if c.timeout > 0 {
		c.conn.SetWriteDeadline(time.Now().Add(c.timeout))
	}

	// Send the frame
	_, err = c.conn.Write(frame)
	if err != nil {
		c.conn.Close()
		c.conn = nil
		return fmt.Errorf("failed to send message: %w", err)
	}

	return nil
}

// ReceiveMessage - Receives and parses a message from the server
// Messages are expected to have a 4-byte length prefix
// Parameters:
//
//	dst - Where to store the parsed message (pointer to a struct)
//
// Returns: Error if receiving or parsing fails
func (c *TCPClient) ReceiveMessage(dst interface{}) error {
	// Check if we're connected
	if c.conn == nil {
		return fmt.Errorf("not connected to server")
	}

	// Set a timeout for this read operation
	if c.timeout > 0 {
		c.conn.SetReadDeadline(time.Now().Add(c.timeout))
	}

	// Step 1: Read the 4-byte length header
	lengthBytes := make([]byte, 4)
	_, err := io.ReadFull(c.conn, lengthBytes)
	if err != nil {
		c.conn.Close()
		c.conn = nil
		return fmt.Errorf("failed to read message length: %w", err)
	}

	// Step 2: Convert the 4 bytes to a number
	messageLength := binary.BigEndian.Uint32(lengthBytes)

	// Step 3: Check if message is too large (prevent memory issues)
	maxMessageSize := uint32(10 * 1024 * 1024) // 10 MB
	if messageLength > maxMessageSize {
		return fmt.Errorf("message too large: %d bytes (max: %d)", messageLength, maxMessageSize)
	}

	// Step 4: Read the actual message data
	messageData := make([]byte, messageLength)
	_, err = io.ReadFull(c.conn, messageData)
	if err != nil {
		c.conn.Close()
		c.conn = nil
		return fmt.Errorf("failed to read message data: %w", err)
	}

	// Step 5: Parse the JSON
	err = json.Unmarshal(messageData, dst)
	if err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}

	return nil
}

// ===== CONNECTION STATUS =====

// IsConnected - Check if we're currently connected
// Returns: true if connected, false otherwise
func (c *TCPClient) IsConnected() bool {
	return c.conn != nil
}

// Close - Close the connection to the server
// Always call this when you're done to cleanup
// Returns: Error if closing fails
func (c *TCPClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// ===== UTILITY METHODS =====

// Ping - Send a PING to the server and wait for a PONG response
// This checks if the server is still responsive
// Returns: Error if ping fails or we don't get a PONG
func (c *TCPClient) Ping() error {
	// Create a PING message
	pingMsg := map[string]interface{}{
		"type":      "PING",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}

	// Send the PING
	if err := c.SendMessage(pingMsg); err != nil {
		return err
	}

	// Wait for the PONG response
	var response map[string]interface{}
	if err := c.ReceiveMessage(&response); err != nil {
		return err
	}

	// Check that we got a PONG
	messageType, ok := response["type"].(string)
	if !ok || messageType != "PONG" {
		return fmt.Errorf("expected PONG but got: %v", response)
	}

	return nil
}
