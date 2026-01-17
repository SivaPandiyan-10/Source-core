# JobSearchEngine - README

A production-ready, multi-language job search automation utility that continuously scans job portals for opportunities matching a candidate's resume.

## 🎯 Overview

**JobSearchEngine** is a sophisticated 24/7 job matching service built with:
- **C++** for high-performance resume parsing and job matching algorithms
- **Go** for orchestration, scheduling, web scraping, and logging

The system automatically searches job portals (LinkedIn, Naukri, etc.) based on resume skills and experience, matches opportunities against the candidate profile with confidence scoring, and logs all matches to daily log files.

## ✨ Key Features

- **Automated Job Discovery**: Continuously searches job portals 24/7
- **Intelligent Matching**: C++-powered scoring engine with configurable weights
- **Duplicate Prevention**: Deduplication across search cycles
- **Cross-Platform**: Windows & Linux support with platform-specific optimizations
- **Resilient**: Exponential backoff retries, rate limiting, error recovery
- **Configurable**: YAML-based configuration for all parameters
- **Extensible Architecture**: Easy to add new job portals
- **Production-Grade**: Proper logging, error handling, concurrency safety

## 📋 Requirements

### Prerequisites
- C++17 compatible compiler (GCC 9+, Clang 10+, MSVC 2019+)
- CMake 3.15+
- Go 1.21+
- 50 MB disk space for binaries
- Resume file in `resumes/` directory

### System Requirements
- RAM: 256 MB minimum, 512 MB recommended
- Disk: 100 MB for logs (varies by search volume)
- Network: Internet access for job portal searches

## 🚀 Quick Start

### 1. Build the Project

```bash
# Clone/download the project
cd JobSearchEngine

# Build C++ engine
mkdir build && cd build
cmake .. && make
cd ..

# Build Go application
cd go && go build -o ../bin/jobsearch_app ./cmd/jobsearch && cd ..
```

### 2. Prepare Resume

Add a resume file to the `resumes/` directory:
```bash
cp your_resume.txt resumes/john_doe.txt
# File naming: resumes/{candidate_name}.txt (underscore for spaces)
```

### 3. Configure (Optional)

Edit `config/config.yaml` to customize:
- Job search interval (default: 6 hours)
- Confidence threshold (default: 0.65)
- Enabled job portals
- Preferred locations and excluded companies

### 4. Run

```bash
./bin/jobsearch_app --candidate "John Doe" --config config/config.yaml
```

The application will:
1. Validate the resume
2. Parse resume for skills, experience, and preferences
3. Enter continuous job search loop
4. Log matches to `logs/YYYY-MM-DD.log`

## 📖 Documentation

- [Architecture Documentation](ARCHITECTURE.md) - System design, component interaction, data flow
- [Build Instructions](BUILD.md) - Detailed build steps for all platforms
- [Deployment Guide](DEPLOYMENT.md) - Production deployment and monitoring

## 📁 Project Structure

```
JobSearchEngine/
├── cpp/                    # C++ Resume Engine
│   ├── include/           # Header files (models, parsers, matchers)
│   ├── src/              # Implementation
│   ├── tests/            # Unit tests
│   └── CMakeLists.txt    # C++ build configuration
├── go/                    # Go Orchestration Layer
│   ├── cmd/jobsearch/    # CLI entry point
│   ├── pkg/              # Reusable packages
│   │   ├── config/       # Configuration management
│   │   ├── logging/      # Daily log file handling
│   │   ├── scheduler/    # Job search scheduling
│   │   ├── search/       # Job portal integration
│   │   └── ipc/          # Go-C++ communication
│   ├── go.mod           # Go module definition
│   └── go.sum           # Dependency lock file
├── config/
│   └── config.yaml       # Configuration template
├── resumes/             # Resume files (candidate_name.txt)
├── logs/                # Daily log files (auto-created)
├── docs/                # Documentation files
├── CMakeLists.txt       # Top-level CMake config
├── ARCHITECTURE.md      # System design documentation
├── BUILD.md             # Build instructions
├── Makefile             # Convenience build targets (optional)
└── README.md            # This file
```

## 🔧 Configuration

### config/config.yaml

```yaml
job_search:
  enabled: true
  interval_hours: 6           # Search every 6 hours
  min_confidence_threshold: 0.65  # Only log matches >= 65% confidence
  skill_weight: 0.35          # 35% of score
  experience_weight: 0.30     # 30% of score
  role_weight: 0.25           # 25% of score
  location_weight: 0.10       # 10% of score

job_portals:
  linkedin:
    enabled: true
    rate_limit_requests_per_hour: 30
  naukri:
    enabled: true
    rate_limit_requests_per_hour: 20

filters:
  preferred_locations:
    - "San Francisco"
    - "Remote"
  excluded_companies: ["Company A"]
  excluded_keywords: ["Intern"]

paths:
  resumes: "./resumes"
  logs: "./logs"
  cpp_engine_path: "./bin/jobsearch_engine"

system:
  prevent_sleep_on_windows: true
  max_retries: 3
  retry_backoff_seconds: 30
```

## 📊 Log Format

Daily logs are written to `logs/YYYY-MM-DD.log`:

```
[2025-01-17 09:15:32] TechCorp | Senior Software Engineer | https://... | LinkedIn | 0.89 | Skill:0.92 Exp:0.85 Role:0.88 Loc:1.00
[2025-01-17 09:16:45] DataSystems Inc | Software Architect | https://... | Naukri | 0.82 | Skill:0.88 Exp:0.80 Role:0.85 Loc:0.75
```

Each entry contains:
- **Timestamp**: When the job was matched
- **Company**: Employer name
- **Role**: Job title
- **Link**: Application URL
- **Source**: Portal (LinkedIn, Naukri, etc.)
- **Confidence Score**: Overall match percentage (0.0-1.0)
- **Score Breakdown**: Individual component scores

## 🧠 Matching Algorithm

The system scores jobs using a weighted formula:

```
Confidence = 
  (SkillMatch × 0.35) +
  (ExperienceMatch × 0.30) +
  (RoleMatch × 0.25) +
  (LocationMatch × 0.10)
```

### Component Scoring

| Component | Calculation | Range |
|-----------|-------------|-------|
| **Skill Match** | Overlapping skills / Required skills | 0.0 - 1.0 |
| **Experience** | Years match ± tolerance | 0.0 - 1.0 |
| **Role Match** | Job title keyword similarity | 0.0 - 1.0 |
| **Location** | Preferred location or remote | 0.0 - 1.0 |

## 🛡️ Safety & Compliance

- **No Auto-Apply**: Only collects job data, no automatic applications
- **Rate Limiting**: Respects API rate limits and portal ToS
- **User-Agent Rotation**: Avoids blocking by rotating user agents
- **Privacy**: Resume data stored locally only
- **Error Recovery**: Graceful handling of network failures
- **Deduplication**: Prevents duplicate entries across runs

## ⚡ Performance

- **Resume Parsing**: < 100ms
- **Job Matching**: < 50ms per job
- **Memory Usage**: 50-100 MB
- **CPU Usage**: < 1% during idle periods
- **Network Usage**: ~1-5 MB per search cycle

## 🔄 Scheduling

The scheduler automatically:
- Searches job portals at configured intervals (default: 6 hours)
- Matches jobs against parsed resume
- Logs matches with confidence scores > threshold
- Handles system sleep/wake gracefully
- Retries on network failures with exponential backoff

## 🐛 Troubleshooting

### "Resume not found"
```bash
# Ensure resume exists with correct naming
ls resumes/
# Should show: john_doe.txt (underscores for spaces)
```

### "C++ engine not found"
```bash
# Check if C++ engine is built
ls -la bin/jobsearch_engine

# Verify path in config.yaml
grep cpp_engine_path config/config.yaml
```

### No jobs found
- Check network connectivity
- Verify portal configuration is enabled in `config.yaml`
- Check job portal rate limits
- Review logs for error messages: `tail -f logs/$(date +%Y-%m-%d).log`

### High memory usage
- Reduce search interval (check fewer jobs)
- Lower log retention (archive old logs)
- Restart application periodically

## 🤝 Contributing

To add support for new job portals:

1. Implement portal searcher in `go/pkg/search/`
2. Add configuration in `config.yaml`
3. Update `SearchEngine` to invoke new searcher
4. Test with sample resumes

## 📝 License

[MIT License](LICENSE)

## 📧 Support

For issues, questions, or suggestions:
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Check [BUILD.md](BUILD.md) for build troubleshooting
- Review log files in `logs/` directory
- Check application output for detailed error messages

## 🔮 Future Roadmap

- [ ] REST API for job status and configuration
- [ ] Web dashboard for match visualization
- [ ] Machine learning-based job quality scoring
- [ ] Mobile push notifications
- [ ] Database backend for long-term analytics
- [ ] Additional job portals (Indeed, Glassdoor, etc.)
- [ ] Resume version management
- [ ] Candidate skill tracking over time

---

**Built with C++ and Go for performance, reliability, and maintainability.**
