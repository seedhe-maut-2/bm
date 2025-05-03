#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <cstring>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sched.h>

#define PACKET_SIZE 1024
#define BURST_SIZE 50

class UDPLoadGenerator {
public:
    UDPLoadGenerator(const std::string& ip, int port, int duration, int threads)
        : target_ip(ip), target_port(port),
          duration_seconds(duration), thread_count(threads) {}

    void run() {
        std::cout << "Starting UDP flood to " << target_ip << ":" << target_port
                  << " for " << duration_seconds << "s using " << thread_count << " threads\n";

        std::vector<std::thread> workers;
        workers.reserve(thread_count);

        for (int i = 0; i < thread_count; ++i) {
            workers.emplace_back([this, i]() {
                pin_thread(i);
                worker_thread();
            });
        }

        // Monitor thread
        std::thread monitor([this]() {
            auto start = std::chrono::steady_clock::now();
            while (running) {
                std::this_thread::sleep_for(std::chrono::seconds(1));
                print_stats(start);
            }
        });

        // Let workers run
        std::this_thread::sleep_for(std::chrono::seconds(duration_seconds));
        running = false;

        for (auto& t : workers) {
            t.join();
        }
        monitor.join();

        print_final_stats();
    }

private:
    std::string target_ip;
    int target_port;
    int duration_seconds;
    int thread_count;
    std::atomic<bool> running{true};
    std::atomic<uint64_t> packets_sent{0};
    std::atomic<uint64_t> bytes_sent{0};

    void pin_thread(int core) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(core % std::thread::hardware_concurrency(), &cpuset);
        pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    }

    void worker_thread() {
        int sock = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK, 0);
        if (sock < 0) {
            perror("socket creation failed");
            return;
        }

        // Turbo socket options
        int buf_size = 1024 * 1024; // 1MB buffer
        setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));

        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(target_port);
        inet_pton(AF_INET, target_ip.c_str(), &addr.sin_addr);

        char buffer[PACKET_SIZE];
        memset(buffer, 'X', sizeof(buffer));

        while (running) {
            // Send packets in bursts
            for (int i = 0; i < BURST_SIZE && running; ++i) {
                ssize_t sent = sendto(sock, buffer, sizeof(buffer), 0,
                                    (struct sockaddr*)&addr, sizeof(addr));
                if (sent > 0) {
                    packets_sent++;
                    bytes_sent += sent;
                }
            }
        }
        close(sock);
    }

    void print_stats(auto start) {
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - start).count();
        double mbps = (bytes_sent * 8.0) / (elapsed * 1024 * 1024);
        std::cout << "\r[STATS] " << packets_sent << " pkts | "
                  << std::fixed << std::setprecision(2) << mbps << " Mbps | "
                  << thread_count << " threads" << std::flush;
    }

    void print_final_stats() {
        double mbps = (bytes_sent * 8.0) / (duration_seconds * 1024 * 1024);
        std::cout << "\n\n=== TEST COMPLETE ===\n"
                  << "Target: " << target_ip << ":" << target_port << "\n"
                  << "Duration: " << duration_seconds << "s\n"
                  << "Threads: " << thread_count << "\n"
                  << "Total Packets: " << packets_sent << "\n"
                  << "Throughput: " << mbps << " Mbps\n"
                  << "Packet Rate: " << packets_sent/duration_seconds << " pps\n";
    }
};

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <ip> <port> <duration> <threads>\n"
                  << "Example: " << argv[0] << " 192.168.1.100 9000 30 8\n";
        return 1;
    }

    try {
        UDPLoadGenerator generator(argv[1], std::stoi(argv[2]), 
                                 std::stoi(argv[3]), std::stoi(argv[4]));
        generator.run();
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
