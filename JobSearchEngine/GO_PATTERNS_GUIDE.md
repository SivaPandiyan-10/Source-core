# Go Patterns Guide for JobSearchEngine

This guide explains the common Go programming patterns used throughout the JobSearchEngine project. Since you're new to Go, this will help you understand the code better.

---

## 1. Structs (Data Structures)

### What's a Struct?
A struct is like a container that holds related data together.

**Example from `tcp_client.go`:**
```go
type TCPClient struct {
    address    string        // Server address like "localhost:10000"
    conn       net.Conn      // The actual network connection
    timeout    time.Duration // How long to wait
}
```

This says: "A TCPClient contains three pieces of information: an address (text), a connection (network object), and a timeout (time)."

### Using Structs
```go
client := &TCPClient{
    address: "localhost:10000",
    timeout: 10 * time.Second,
}
```

The `&` means "give me a pointer to this struct" (like a reference to the data in memory).

---

## 2. Methods (Functions That Belong to a Struct)

### What's a Method?
A method is a function that works with a specific struct. It's like saying "this function belongs to this data."

**Syntax:**
```go
func (c *TCPClient) IsConnected() bool {
    return c.conn != nil
}
```

Breaking it down:
- `(c *TCPClient)` = "This method works with a TCPClient, and `c` is the variable name"
- `*` = "It's a pointer to TCPClient" (can modify the original data)
- `IsConnected()` = method name
- `bool` = returns a boolean (true/false)

### Calling a Method
```go
client := &TCPClient{}
if client.IsConnected() {
    fmt.Println("Connected!")
}
```

---

## 3. Error Handling

### The Go Way: "Explicit is Better Than Implicit"
In Go, functions that can fail return two things: the result and an error.

**Example:**
```go
func (c *TCPClient) Connect(ctx context.Context) error {
    conn, err := dialer.DialContext(ctx, "tcp", c.address)
    if err != nil {
        return fmt.Errorf("failed to connect: %w", err)
    }
    c.conn = conn
    return nil
}
```

This says:
- Try to connect with `DialContext()`
- If it fails, `err` will contain the error
- Check if `err` is not nil (meaning it failed)
- If it failed, create a new error message and return it
- If it succeeded, do the work and return `nil` (no error)

### Calling a Function That Returns an Error
```go
if err := client.Connect(ctx); err != nil {
    fmt.Println("Connection failed:", err)
    return
}
// Connection succeeded, continue...
```

### Error Wrapping with %w
```go
fmt.Errorf("failed to connect: %w", originalError)
```

This keeps the original error message so you know exactly what went wrong. It's like saying "this thing failed, and here's why..." (the `%w` includes the original reason).

---

## 4. Goroutines (Concurrent Tasks)

### What's a Goroutine?
A goroutine is a lightweight thread - a task that runs at the same time as other code.

**Example from orchestrator.go:**
```go
o.wg.Add(3)              // We're about to start 3 goroutines
go o.scheduleJobFetching()    // Start 1st task
go o.healthCheckWorker()      // Start 2nd task
go o.handleShutdown()         // Start 3rd task

// All three run at the same time!
```

The `go` keyword says "run this function in the background, don't wait for it to finish."

### WaitGroup: Waiting for Goroutines to Finish
```go
var wg sync.WaitGroup

wg.Add(3)  // We're starting 3 goroutines
go func() {
    defer wg.Done()  // Signal when this goroutine finishes
    // Do work here
}()

wg.Wait()  // Wait for all 3 to finish before continuing
```

- `wg.Add(3)` = "I'm about to start 3 goroutines"
- `defer wg.Done()` = "When this function ends, tell the WaitGroup"
- `wg.Wait()` = "Don't continue until all goroutines call Done()"

---

## 5. Channels (Communication Between Goroutines)

### What's a Channel?
A channel is like a pipe - it lets goroutines send messages to each other.

**Example from orchestrator.go:**
```go
sigChan := make(chan os.Signal, 1)  // Create a channel for signals
signal.Notify(sigChan, os.Interrupt) // Listen for Ctrl+C

go func() {
    <-sigChan  // Wait for a signal (read from channel)
    orch.Stop() // Then stop
}()
```

- `make(chan os.Signal, 1)` = "Create a channel that holds signals"
- `<-sigChan` = "Read from the channel (wait for a signal)"
- `signal.Notify()` = "When Ctrl+C happens, send it to the channel"

### Select Statement: Multiple Channels
The `select` statement watches multiple channels and does something when one fires.

**Example from tcp_client.go:**
```go
for {
    select {
    case <-ctx.Done():
        // Context was cancelled, stop retrying
        return ctx.Err()
    case <-time.After(waitTime):
        // Timer fired, try connecting again
        if err := c.Connect(ctx); err == nil {
            return nil
        }
    }
}
```

This says:
- Watch two channels
- If `ctx.Done()` fires (shutdown signal), stop
- If `time.After()` fires (timer done), try connecting again

---

## 6. Context (Cancellation and Timeouts)

### What's Context?
Context is used to:
1. Cancel operations when you want to stop
2. Set timeouts (max wait time)
3. Pass values between functions

**Example from orchestrator.go:**
```go
ctx, cancel := context.WithCancel(context.Background())
// ... later ...
cancel()  // This causes ctx.Done() to fire everywhere
```

### Context in a Loop
```go
for {
    select {
    case <-ctx.Done():
        // Cancel was called, exit the loop
        return
    case <-ticker.C:
        // Do work
    }
}
```

### Timeouts
```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

conn, err := dialer.DialContext(ctx, "tcp", "localhost:10000")
// If it takes more than 30 seconds, automatically times out
```

---

## 7. JSON Marshaling (Converting to/from JSON)

### Structs to JSON
```go
type Message struct {
    Type string `json:"type"`
    ID   int    `json:"id"`
}

msg := Message{Type: "PING", ID: 123}
jsonBytes, err := json.Marshal(msg)
// Result: []byte(`{"type":"PING","id":123}`)
```

The backticks (`` `json:"type"` ``) tell Go: "When converting to JSON, use this name instead."

### JSON to Structs
```go
jsonText := []byte(`{"type":"PONG","id":123}`)
var response Message
json.Unmarshal(jsonText, &response)
// response.Type is now "PONG"
// response.ID is now 123
```

The `&response` means "give me a pointer so I can modify the struct."

---

## 8. Interfaces (Flexible Functions)

Interfaces define what a thing CAN DO, not what it IS.

**Example:**
```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

This says: "Anything that has a Read method is a Reader, no matter what it actually is."

Any file, network connection, or buffer can be a Reader because they all have a `Read` method.

---

## 9. Mutex (Protecting Shared Data)

A Mutex (mutual exclusion) prevents multiple goroutines from accessing data at the same time.

**Example from logger.go:**
```go
type Logger struct {
    mu   sync.Mutex
    file *os.File
}

func (l *Logger) LogMatch(entry LogEntry) error {
    l.mu.Lock()         // Lock: only I can access the file now
    defer l.mu.Unlock() // Unlock: when this function ends, let others use it
    
    // Use l.file safely here
    l.file.WriteString(line)
    
    return nil
}
```

- `Lock()` = "Give me exclusive access to this data"
- `Unlock()` = "I'm done, others can use it now"
- `defer Unlock()` = "Always unlock, even if there's an error"

Without mutex, if two goroutines write to the file at the same time, the data gets corrupted.

---

## 10. Map: Key-Value Storage

A map is like a dictionary - find values by keys.

**Example from orchestrator.go:**
```go
var processedJobIDs sync.Map

// Store a value
processedJobIDs.Store("job-123", true)

// Check if key exists
if _, exists := processedJobIDs.Load("job-123"); exists {
    fmt.Println("Already processed this job")
}
```

`sync.Map` is used when multiple goroutines access it at the same time (thread-safe).

---

## 11. Defer: Cleanup Operations

`defer` says "run this function when the current function ends, no matter what happens."

**Example from tcp_client.go:**
```go
func (c *TCPClient) SendMessage(msg interface{}) error {
    if c.conn == nil {
        return fmt.Errorf("not connected")
    }
    
    if c.timeout > 0 {
        c.conn.SetWriteDeadline(time.Now().Add(c.timeout))
    }
    
    _, err := c.conn.Write(frame)
    if err != nil {
        c.conn.Close()  // Close if error
        c.conn = nil
        return fmt.Errorf("failed to send message: %w", err)
    }

    return nil
}
```

And from logger.go:
```go
func (l *Logger) LogMatch(entry LogEntry) error {
    l.mu.Lock()
    defer l.mu.Unlock()  // Always unlock, even if LogMatch fails
    
    // Work with file...
}
```

**Why use defer?**
- Guarantees cleanup happens
- Clearer code (the cleanup is near the acquisition)
- Works even if there are multiple return statements or panics

---

## 12. Type Assertions: Treating Interfaces as Specific Types

When you have an `interface{}` (anything), sometimes you need to treat it as a specific type.

**Example from orchestrator.go:**
```go
var response map[string]interface{}
// Parse JSON...

messageType, ok := response["type"].(string)
if !ok {
    return fmt.Errorf("type is not a string")
}
```

`response["type"].(string)` means: "Treat this value as a string, and tell me if it worked."

The `ok` variable is `true` if the conversion worked, `false` if it didn't.

---

## 13. Pattern: Exponential Backoff (Retrying with Increasing Delays)

When something fails, retry, but wait longer each time.

**Example from tcp_client.go:**
```go
waitTime := time.Second     // Start with 1 second
maxWaitTime := time.Minute  // Don't wait more than 1 minute

for attempt := 0; attempt < maxAttempts; attempt++ {
    if err := c.Connect(ctx); err == nil {
        return nil  // Success!
    }
    
    if attempt < maxAttempts-1 {
        select {
        case <-time.After(waitTime):
            // Wait, then try again
        case <-ctx.Done():
            return ctx.Err()  // Cancelled
        }
        
        // Increase wait time for next attempt
        waitTime = waitTime * 2
        if waitTime > maxWaitTime {
            waitTime = maxWaitTime
        }
    }
}
```

Attempt 1: Wait 1 second
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
Attempt 4: Wait 8 seconds
...
(never wait more than 1 minute)

This is smart because:
- First attempts try quickly
- Later attempts give the server more time to recover
- Doesn't hammer the server with connection attempts

---

## 14. Pattern: Event Loop with Ticker

Periodically do something.

**Example from orchestrator.go:**
```go
scheduleTicker := time.NewTicker(1 * time.Hour)
defer scheduleTicker.Stop()

for {
    select {
    case <-ctx.Done():
        return  // Stop the loop
    case <-scheduleTicker.C:
        o.fetchAndProcessJobs()  // Do work every hour
    }
}
```

This runs `fetchAndProcessJobs()` every hour, but can stop immediately if `ctx.Done()` happens.

---

## 15. Pattern: Health Check Worker

Monitor something in the background.

**Example from orchestrator.go:**
```go
func (o *Orchestrator) healthCheckWorker() {
    defer o.wg.Done()
    
    for {
        select {
        case <-o.ctx.Done():
            return
        case <-o.healthCheckTick.C:
            if !o.tcpClient.IsConnected() {
                // Reconnect
                o.tcpClient.ConnectWithRetry(o.ctx)
            } else {
                // Ping to make sure it's responsive
                o.tcpClient.Ping()
            }
        }
    }
}
```

This runs in a separate goroutine and:
- Checks if connected every 5 minutes
- Reconnects if needed
- Pings the server if connected

---

## Summary: The JobSearchEngine Flow

1. **main.go** reads config and starts the orchestrator
2. **orchestrator.go** starts 3 goroutines:
   - `scheduleJobFetching()` - every hour, fetch jobs
   - `healthCheckWorker()` - every 5 minutes, check if server is alive
   - `handleShutdown()` - wait for Ctrl+C
3. **tcp_client.go** handles communication with C++ server
   - Uses exponential backoff for reconnection
   - Sends/receives length-prefixed JSON
4. **logger.go** logs matched jobs daily
   - Creates new file each day
   - Uses Mutex to prevent corruption
5. **platform/** module fetches jobs from LinkedIn, Naukri, etc.

All goroutines communicate via:
- Channels (for shutdown signals)
- Context (for cancellation and timeouts)
- Methods on shared objects (with Mutex protection)

---

## Common Go Idioms in This Project

| Idiom | Meaning | Example |
|-------|---------|---------|
| `if err != nil { return err }` | Check if operation failed | Connection failed |
| `defer cleanup()` | Always run cleanup | Unlock mutex, close file |
| `go func() {}()` | Run in background | Start health check |
| `<-ctx.Done()` | Wait for cancellation | Stop gracefully |
| `select { case ...: }` | Wait for multiple channels | React to timer or cancel |
| `&variable` | Get pointer to variable | Pass data to function |
| `arr[index]` | Access array/map | Get config value |
| `var x interface{}` | Accept anything | Generic JSON parsing |
| `x.(Type)` | Convert interface to type | Check if value is string |
| `close(channel)` | End channel | (not used in this project) |

---

## Tips for Understanding the Code

1. **Start with main.go** - See the overall flow
2. **Follow the comments** - Each function has comments explaining what it does
3. **Read the section headers** - Code is organized into ===== SECTIONS =====
4. **Look for patterns** - Error handling, context usage, goroutines follow patterns
5. **Trace the data** - Follow how data flows from one function to another
6. **Google the functions** - Don't know what `json.Marshal` does? Search it!

---

## Questions to Ask While Reading

- Why does this function return an error?
- Why is this data protected by a Mutex?
- Why is this code running in a goroutine?
- What would happen if we removed this defer?
- What happens when ctx.Done() fires?

Good luck with Go! 🚀
