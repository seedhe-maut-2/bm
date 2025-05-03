#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <cstring>
#include <cmath>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <iomanip>
#include <sstream>

/*
 * =============================================
 * ULTRA HIGH-PERFORMANCE UDP LOAD GENERATOR
 * ---------------------------------------------
 * Owner: @seedhe_maut
 * Expiry Date: 4 May 2024
 * Version: 2.0 (Turbo Mode)
 * =============================================
 */

class UDPLoadGenerator {
public:
    struct Config {
        std::string target_ip = "127.0.0.1";
        uint16_t target_port = 12345;
        size_t packet_size = 512;
        size_t packets_per_second = 100000;
        size_t burst_interval_us = 100;
        size_t burst_size = 50;
        size_t duration_seconds = 30;
        size_t thread_count = 8;
        bool turbo_mode = true;
        bool verbose = false;
    };

    struct Stats {
        std::atomic<uint64_t> total_packets_sent{0};
        std::atomic<uint64_t> total_latency_ns{0};
        std::atomic<uint64_t> total_bytes_sent{0};
        std::atomic<uint64_t> send_errors{0};
        std::atomic<uint64_t> min_latency_ns{UINT64_MAX};
        std::atomic<uint64_t> max_latency_ns{0};
    };

    UDPLoadGenerator(const Config& config) : config_(config) {
        print_banner();
        
        // Validate configuration
        if (config_.thread_count == 0 || config_.thread_count > 1000) {
            throw std::runtime_error("Thread count must be between 1 and 1000");
        }
        if (config_.packet_size < 8 || config_.packet_size > 65507) {
            throw std::runtime_error("Packet size must be between 8 and 65507 bytes");
        }
        if (config_.burst_interval_us < 10 || config_.burst_interval_us > 1000000) {
            throw std::runtime_error("Burst interval must be between 10 and 1000000 microseconds");
        }

        if (config_.turbo_mode) {
            std::cout << "[+] Turbo Mode: Activated\n";
        }
    }

    void run() {
        auto start_time = std::chrono::steady_clock::now();
        
        // Initialize threads
        std::vector<std::thread> workers;
        workers.reserve(config_.thread_count);

        // Create thread-local sockets and buffers
        for (size_t i = 0; i < config_.thread_count; ++i) {
            workers.emplace_back([this, i]() {
                worker_thread(i);
            });

            // Pin threads to CPU cores for better performance
            if (config_.turbo_mode) {
                cpu_set_t cpuset;
                CPU_ZERO(&cpuset);
                CPU_SET(i % std::thread::hardware_concurrency(), &cpuset);
                pthread_setaffinity_np(workers.back().native_handle(), sizeof(cpu_set_t), &cpuset);
            }
        }

        // Progress monitoring thread
        std::thread monitor_thread([this, start_time]() {
            progress_monitor(start_time);
        });

        // Wait for all worker threads
        for (auto& worker : workers) {
            worker.join();
        }

        // Stop the monitor thread
        monitoring_active_ = false;
        monitor_thread.join();

        // Print final results
        print_results(start_time);
    }

private:
    void print_banner() {
        std::cout << R"(
  _   _ _____ ____  ____       _       _____                           _             
 | | | |  ___|  _ \|  _ \  ___| |_ __ |  ___| __ __ _ _ __  ___ _ __ | |_ ___ _ __ 
 | | | | |_  | | | | | | |/ _ \ | '_ \| |_ | '__/ _` | '_ \/ __| '_ \| __/ _ \ '__|
 | |_| |  _| | |_| | |_| |  __/ | |_) |  _|| | | (_| | | | \__ \ |_) | ||  __/ |   
  \___/|_|   |____/|____/ \___|_| .__/|_|  |_|  \__,_|_| |_|___/ .__/ \__\___|_|   
                                |_|                             |_|                 
)" << std::endl;
        std::cout << "Owner: @seedhe_maut | Expiry: 4 May 2024 | Version: 2.0 Turbo\n\n";
    }

    void worker_thread(size_t thread_id) {
        // Create socket for this thread
        int sock = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK, IPPROTO_UDP);
        if (sock < 0) {
            perror("socket creation failed");
            return;
        }

        // Turbo mode optimizations
        if (config_.turbo_mode) {
            int buf_size = 1024 * 1024; // 1MB buffer
            setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));
            
            int val = 1;
            setsockopt(sock, SOL_SOCKET, SO_REUSEPORT, &val, sizeof(val));
        }

        // Configure target address
        struct sockaddr_in target_addr;
        memset(&target_addr, 0, sizeof(target_addr));
        target_addr.sin_family = AF_INET;
        target_addr.sin_port = htons(config_.target_port);
        if (inet_pton(AF_INET, config_.target_ip.c_str(), &target_addr.sin_addr) <= 0) {
            perror("invalid address");
            close(sock);
            return;
        }

        // Prepare packet buffer with timestamp (first 16 bytes)
        std::vector<char> buffer(config_.packet_size);
        uint64_t sequence_number = (thread_id + 1) << 48; // Use high bits for thread ID

        // Calculate timing parameters
        const double packets_per_thread_per_second = static_cast<double>(config_.packets_per_second) / config_.thread_count;
        const size_t packets_per_burst = config_.burst_size > 0 ? config_.burst_size : 
            static_cast<size_t>(std::ceil(packets_per_thread_per_second * config_.burst_interval_us / 1000000.0));
        
        const auto burst_interval = std::chrono::microseconds(config_.burst_interval_us);
        auto next_burst_time = std::chrono::steady_clock::now();
        auto end_time = next_burst_time + std::chrono::seconds(config_.duration_seconds);

        while (std::chrono::steady_clock::now() < end_time) {
            // Send burst of packets
            for (size_t i = 0; i < packets_per_burst; ++i) {
                // Write metadata to packet
                const auto send_time = std::chrono::steady_clock::now();
                *reinterpret_cast<uint64_t*>(buffer.data()) = sequence_number++;
                *reinterpret_cast<uint64_t*>(buffer.data() + 8) = std::chrono::duration_cast<std::chrono::nanoseconds>(
                    send_time.time_since_epoch()).count();

                // Send packet
                ssize_t sent = sendto(sock, buffer.data(), buffer.size(), 0,
                                    (struct sockaddr*)&target_addr, sizeof(target_addr));
                
                if (sent > 0) {
                    auto latency = std::chrono::steady_clock::now() - send_time;
                    auto latency_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(latency).count();

                    stats_.total_packets_sent++;
                    stats_.total_latency_ns += latency_ns;
                    stats_.total_bytes_sent += sent;

                    // Update min/max latency
                    uint64_t current_min = stats_.min_latency_ns.load();
                    while (latency_ns < current_min && 
                          !stats_.min_latency_ns.compare_exchange_weak(current_min, latency_ns)) {}

                    uint64_t current_max = stats_.max_latency_ns.load();
                    while (latency_ns > current_max && 
                          !stats_.max_latency_ns.compare_exchange_weak(current_max, latency_ns)) {}
                } else {
                    stats_.send_errors++;
                }
            }

            // Sleep until next burst
            next_burst_time += burst_interval;
            if (next_burst_time > std::chrono::steady_clock::now()) {
                std::this_thread::sleep_until(next_burst_time);
            } else if (config_.verbose) {
                std::cerr << "Thread " << thread_id << " can't keep up with requested rate\n";
            }
        }

        close(sock);
    }

    void progress_monitor(std::chrono::steady_clock::time_point start_time) {
        auto last_time = start_time;
        uint64_t last_packets = 0;
        uint64_t last_bytes = 0;

        while (monitoring_active_) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::duration<double>>(now - last_time).count();
            
            uint64_t current_packets = stats_.total_packets_sent.load();
            uint64_t current_bytes = stats_.total_bytes_sent.load();
            
            uint64_t delta_packets = current_packets - last_packets;
            uint64_t delta_bytes = current_bytes - last_bytes;
            
            double pps = delta_packets / elapsed;
            double mbps = (delta_bytes * 8.0) / (elapsed * 1024 * 1024);

            std::cout << "\r[STATS] "
                      << "Pkts: " << current_packets << " ("
                      << std::fixed << std::setprecision(1) << pps/1000 << "Kpps) | "
                      << "BW: " << mbps << " Mbps | "
                      << "Errors: " << stats_.send_errors.load() << "   " << std::flush;

            last_time = now;
            last_packets = current_packets;
            last_bytes = current_bytes;
        }
    }

    void print_results(std::chrono::steady_clock::time_point start_time) {
        auto end_time = std::chrono::steady_clock::now();
        double duration = std::chrono::duration_cast<std::chrono::duration<double>>(end_time - start_time).count();

        uint64_t total_packets = stats_.total_packets_sent.load();
        uint64_t total_latency = stats_.total_latency_ns.load();
        uint64_t total_bytes = stats_.total_bytes_sent.load();
        uint64_t send_errors = stats_.send_errors.load();
        uint64_t min_latency = stats_.min_latency_ns.load();
        uint64_t max_latency = stats_.max_latency_ns.load();

        double avg_latency_ns = total_packets > 0 ? static_cast<double>(total_latency) / total_packets : 0;
        double packets_per_sec = total_packets / duration;
        double mbps = (total_bytes * 8.0) / (duration * 1024 * 1024);

        std::cout << "\n\n=== FINAL RESULTS ===" << std::endl;
        std::cout << "Test Duration:      " << std::fixed << std::setprecision(3) << duration << " seconds\n";
        std::cout << "Total Packets:      " << total_packets << "\n";
        std::cout << "Total Bytes:        " << format_bytes(total_bytes) << "\n";
        std::cout << "Throughput:         " << std::fixed << std::setprecision(1) 
                  << packets_per_sec/1000 << " Kpps (" << mbps << " Mbps)\n";
        std::cout << "Latency (min/avg/max): " 
                  << min_latency/1000.0 << " / " 
                  << avg_latency_ns/1000.0 << " / " 
                  << max_latency/1000.0 << " µs\n";
        std::cout << "Send Errors:        " << send_errors << "\n";
        std::cout << "=================================\n";
    }

    std::string format_bytes(uint64_t bytes) {
        const char* units[] = {"B", "KB", "MB", "GB", "TB"};
        double size = bytes;
        int unit = 0;

        while (size >= 1024 && unit < 4) {
            size /= 1024;
            unit++;
        }

        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2) << size << " " << units[unit];
        return oss.str();
    }

    const Config config_;
    Stats stats_;
    std::atomic<bool> monitoring_active_{true};
};

int main(int argc, char* argv[]) {
    try {
        UDPLoadGenerator::Config config;

        // Parse command line arguments
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];
            if (arg == "-h" || arg == "--help") {
                std::cout << "Usage: " << argv[0] << " [options]\n"
                          << "Options:\n"
                          << "  -i <ip>        Target IP (default: 127.0.0.1)\n"
                          << "  -p <port>      Target port (default: 12345)\n"
                          << "  -s <size>      Packet size in bytes (default: 512)\n"
                          << "  -r <rate>      Target rate in packets/sec (default: 100000)\n"
                          << "  -t <threads>   Worker threads (default: 8)\n"
                          << "  -d <seconds>   Test duration (default: 30)\n"
                          << "  --turbo        Enable turbo mode (default: on)\n"
                          << "  --verbose      Verbose output\n";
                return 0;
            } else if (arg == "-i" && i+1 < argc) {
                config.target_ip = argv[++i];
            } else if (arg == "-p" && i+1 < argc) {
                config.target_port = static_cast<uint16_t>(std::stoi(argv[++i]));
            } else if (arg == "-s" && i+1 < argc) {
                config.packet_size = static_cast<size_t>(std::stoi(argv[++i]));
            } else if (arg == "-r" && i+1 < argc) {
                config.packets_per_second = static_cast<size_t>(std::stoi(argv[++i]));
            } else if (arg == "-t" && i+1 < argc) {
                config.thread_count = static_cast<size_t>(std::stoi(argv[++i]));
            } else if (arg == "-d" && i+1 < argc) {
                config.duration_seconds = static_cast<size_t>(std::stoi(argv[++i]));
            } else if (arg == "--turbo") {
                config.turbo_mode = true;
            } else if (arg == "--verbose") {
                config.verbose = true;
            }
        }

        UDPLoadGenerator generator(config);
        generator.run();

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << std::endl;
        return 1;
    }
}
