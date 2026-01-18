# Start Here: Your Guide to Reading the Code

Hello! You're new to Go and want to understand this JobSearchEngine project. This guide tells you exactly what to read and in what order.

---

## Learning Path (4 Stages)

### Stage 1: Understand the Big Picture (30 minutes)
**Goal:** Know what the project does and how pieces fit together

**Read these in order:**
1. [README.md](README.md) - What is JobSearchEngine?
2. [GO_QUICK_REFERENCE.md](GO_QUICK_REFERENCE.md) - Project structure section
3. [GO_QUICK_REFERENCE.md](GO_QUICK_REFERENCE.md) - "The Main Flow" section

**After this, you'll know:**
- What the project does
- What each file's purpose is
- How data flows from start to end

---

### Stage 2: Learn Go Language (1-2 hours)
**Goal:** Understand Go concepts before reading code

**Read this:**
- [GO_PATTERNS_GUIDE.md](GO_PATTERNS_GUIDE.md) - Read sections 1-7 first

**Topics to understand:**
1. Structs - How data is organized
2. Methods - Functions that belong to structs
3. Error Handling - The Go way of handling mistakes
4. Goroutines - Running multiple tasks at once
5. Channels - How goroutines talk to each other
6. Context - Cancellation and timeouts
7. JSON - Converting between Go objects and JSON

**Stop here and come back to 8-15 after you've read some code.**

**Tips:**
- Don't memorize everything
- Focus on understanding the concepts
- You'll see these patterns in the actual code

---

### Stage 3: Read the Actual Code (1 hour)
**Goal:** See Go patterns in action

**Read these files in order:**
1. [go/cmd/jobsearch/main.go](go/cmd/jobsearch/main.go)
   - **What:** Entry point of the program
   - **Why first:** Shows how pieces come together
   - **Time:** 10 minutes
   - **Questions:** What's in config? What's created?

2. [go/pkg/orchestrator/orchestrator.go](go/pkg/orchestrator/orchestrator.go)
   - **What:** Main coordinator - the heart of the system
   - **Why second:** Shows the main flow
   - **Time:** 15 minutes
   - **Questions:** What are the 3 goroutines? What's fetchAndProcessJobs?

3. [go/pkg/client/tcp_client.go](go/pkg/client/tcp_client.go)
   - **What:** How Go talks to C++
   - **Why third:** Shows network communication
   - **Time:** 15 minutes
   - **Questions:** How is data sent/received? What's exponential backoff?

4. [go/pkg/logging/logger.go](go/pkg/logging/logger.go)
   - **What:** Saving matched jobs to files
   - **Why fourth:** Shows file I/O and mutex usage
   - **Time:** 10 minutes
   - **Questions:** How does daily rotation work? Why Mutex?

5. [go/pkg/platform/fetcher.go](go/pkg/platform/fetcher.go)
   - **What:** Fetching jobs from LinkedIn, Naukri
   - **Why fifth:** Shows how to add new platforms
   - **Time:** 5 minutes
   - **Questions:** How would I add a new platform?

**Stop and review stage 2 concepts** if anything confuses you.

---

### Stage 4: Deep Dive (2-3 hours, optional)
**Goal:** Master the code and be ready to modify it

**Read sections 8-15 of GO_PATTERNS_GUIDE.md:**
- Interfaces
- Mutexes
- Maps
- Defer
- Type Assertions
- Exponential Backoff (you've seen this!)
- Event Loop with Ticker (you've seen this!)
- Health Check Worker (you've seen this!)
- Error patterns in the code

**Then:**
1. Re-read [orchestrator.go](go/pkg/orchestrator/orchestrator.go) - understand every line
2. Re-read [tcp_client.go](go/pkg/client/tcp_client.go) - understand the backoff
3. Try modifying something simple:
   - Change the fetch interval to 30 minutes
   - Change the health check interval to 10 minutes
   - Add a new print statement
4. Run the code and see it work

---

## Quick Reference While Reading

### When You See...
| Go Code | Look Here |
|---------|-----------|
| `go func()` | GO_PATTERNS_GUIDE.md - Section 4 (Goroutines) |
| `<-channel` | GO_PATTERNS_GUIDE.md - Section 5 (Channels) |
| `ctx.Done()` | GO_PATTERNS_GUIDE.md - Section 6 (Context) |
| `if err != nil` | GO_PATTERNS_GUIDE.md - Section 3 (Error Handling) |
| `json.Marshal` | GO_PATTERNS_GUIDE.md - Section 7 (JSON) |
| `defer` | GO_PATTERNS_GUIDE.md - Section 11 (Defer) |
| `mutex.Lock()` | GO_PATTERNS_GUIDE.md - Section 9 (Mutex) |
| `time.NewTicker()` | GO_PATTERNS_GUIDE.md - Section 14 (Ticker) |
| `select { case ... }` | GO_PATTERNS_GUIDE.md - Section 5 (Channels) |

---

## Reading Tips

### 1. Don't Rush
- Read comments carefully
- Understanding 50 lines deeply > skimming 500 lines
- Go slow, enjoy it

### 2. Use Breakpoints (Mental Checkpoints)
After reading each section, ask yourself:
- "What does this do in one sentence?"
- "Why is this function here?"
- "What would break if I removed this?"

### 3. Google Unfamiliar Functions
```
"golang json.Marshal examples"
"golang goroutines tutorial"
```
Go documentation is excellent - use it!

### 4. Try It Out
```bash
cd go
go run cmd/jobsearch/main.go
```
See the code running. Read the output. Understand it.

### 5. Make Small Changes
```go
// In main.go, change:
fmt.Printf("Server: %s\n", o.config.ServerAddress)
// To:
fmt.Printf("CONNECTING TO SERVER AT: %s\n", o.config.ServerAddress)
```
Recompile and run. See the change. Feel the power!

---

## Common Confusion Points

### Confusion: `*TCPClient` vs `TCPClient`
**Explanation:**
- `TCPClient` - The actual data
- `*TCPClient` - A pointer (reference) to the data
- `&client` - "Give me a pointer to this data"

**In code:**
```go
client := &TCPClient{}     // Create data, get a pointer
client.IsConnected()       // Use it (Go handles the pointer)
```

### Confusion: `json.Marshal` returns what?
**Explanation:**
```go
jsonBytes, err := json.Marshal(msg)
// jsonBytes = the JSON as bytes ([]byte)
// err = error if conversion failed (or nil if success)
```

### Confusion: What's `defer`?
**Explanation:**
"Run this when the function ends, no matter what."

```go
func example() {
    file := openFile()
    defer file.Close()  // Will run at the end
    
    // Do stuff with file...
} // Close runs here automatically
```

### Confusion: What's a goroutine?
**Explanation:**
```go
// Without goroutine (waits for function to finish):
doWork()
fmt.Println("Done!")

// With goroutine (runs in background):
go doWork()
fmt.Println("Started!")  // Prints immediately
```

### Confusion: What's `select`?
**Explanation:**
"Watch multiple channels, do something when one fires."

```go
select {
case msg := <-channelA:
    // Something came from channelA
case <-channelB:
    // Something came from channelB
}
```

---

## Test Your Understanding

After reading, can you answer these?

### Easy (Stage 1-2)
- [ ] What does JobSearchEngine do?
- [ ] Name the 3 goroutines in orchestrator
- [ ] What's a goroutine?
- [ ] What's an error in Go?
- [ ] What does `defer` do?

### Medium (Stage 3)
- [ ] How does Go send a message to C++?
- [ ] What's exponential backoff?
- [ ] Why is Mutex needed in logger?
- [ ] What's the 4-byte length prefix for?
- [ ] How would you add a new job platform?

### Hard (Stage 4)
- [ ] Explain the entire flow from main() to job matching
- [ ] Why does tcpClient need a context?
- [ ] What would happen if we removed the Mutex from logger?
- [ ] How does the health check worker work?
- [ ] What's the format of a TCP message?

**If you can't answer these yet, that's fine!** Re-read the sections and try again.

---

## Learning Mindset

### Remember:
- **Everyone** was confused by goroutines at first
- **Everyone** was confused by channels at first
- **Everyone** had to Google stuff
- **Everyone** took time to understand

### Don't:
- ❌ Try to memorize everything
- ❌ Read code without understanding
- ❌ Skip the comments
- ❌ Give up after first confusion

### Do:
- ✅ Read comments first
- ✅ Understand the WHY before the WHAT
- ✅ Take breaks
- ✅ Run the code and see it work
- ✅ Ask questions
- ✅ Google stuff
- ✅ Be patient with yourself

---

## File Organization

```
JobSearchEngine/
├── README.md                        ← What is this project?
├── GO_PATTERNS_GUIDE.md            ← Learn Go language concepts
├── GO_QUICK_REFERENCE.md           ← Understand the project structure
├── REFACTORING_SUMMARY.md          ← What changed and why
├── START_HERE.md                   ← This file!
├── go/
│   ├── cmd/jobsearch/
│   │   └── main.go                 ← START READING HERE
│   └── pkg/
│       ├── client/tcp_client.go    ← READ SECOND
│       ├── orchestrator/
│       │   └── orchestrator.go     ← READ THIRD
│       ├── logging/logger.go       ← READ FOURTH
│       └── platform/fetcher.go     ← READ FIFTH
├── cpp/                            ← C++ code (can ignore for now)
├── config/orchestrator.json        ← Configuration
└── logs/                           ← Daily job match logs (created at runtime)
```

---

## Time Estimates

| Activity | Time |
|----------|------|
| Stage 1: Big Picture | 30 min |
| Stage 2: Learn Go | 1-2 hours |
| Stage 3: Read Code | 1 hour |
| Stage 4: Deep Dive | 2-3 hours |
| **Total** | **4-6 hours** |

This is a reasonable amount of time to go from "What's Go?" to "I understand the entire project!"

---

## Next: Start Reading!

You're ready! Begin with [GO_QUICK_REFERENCE.md](GO_QUICK_REFERENCE.md).

If you get stuck:
1. Re-read the relevant section
2. Check GO_PATTERNS_GUIDE.md
3. Google it
4. Try to explain it to yourself out loud
5. Take a break and come back

**You've got this!** 🚀

---

## Questions?

If something is unclear:
1. Is there a comment explaining it? (Read carefully)
2. Is it in GO_PATTERNS_GUIDE.md? (Search for the concept)
3. Is it a Go function? (Google "golang functionName")
4. Is it a design choice? (Check REFACTORING_SUMMARY.md)

Happy learning!
